import os
import json
import pandas as pd
import numpy as np
from datetime import timedelta
from lightgbm import LGBMRegressor
from sklearn.metrics import mean_absolute_percentage_error

from scripts.db_connector import DBConnector

ROOT_EXP = "data/processed/expenses"
OUT_DIR = "data/features/expenses"
os.makedirs(OUT_DIR, exist_ok=True)


def evaluate(y_true, y_pred):
    y_true = np.array(y_true, dtype=float)
    y_pred = np.array(y_pred, dtype=float)
    
    if np.allclose(y_true, 0):
        return float("nan"), float(np.sqrt(np.mean((y_true - y_pred) ** 2)))
    
    denom = np.where(np.abs(y_true) < 1e-6, 1e-6, y_true)
    mape = np.mean(np.abs((y_true - y_pred) / denom)) * 100.0
    rmse = float(np.sqrt(np.mean((y_true - y_pred) ** 2)))
    return float(mape), rmse


def load_category_df(user_id, cat):
    fpath = os.path.join(ROOT_EXP, f"{user_id}_{cat}_features.csv")
    if not os.path.exists(fpath):
        return None
    df = pd.read_csv(fpath, parse_dates=["date"])
    if df.empty:
        return None
    return df.sort_values("date").reset_index(drop=True)


def run_lgb(df, horizon=14):
    """Your original LightGBM expense forecasting"""
    temp = df.copy()
    
    feat_cols = [
        "prev_day_net", "lag7_mean", "rolling_7_mean", "rolling_30_mean",
        "rolling_7_std", "rolling_30_std", "dayofweek", "is_weekend",
        "month", "is_month_end", "tx_count",
    ]
    
    for c in feat_cols:
        if c not in temp.columns:
            temp[c] = 0.0
    
    temp["target"] = temp["net_amt"].shift(-1)
    train = temp.dropna(subset=["target"]).reset_index(drop=True)
    
    if train.empty:
        last_date = temp["date"].max()
        last_val = float(temp["net_amt"].iloc[-1])
        future_dates = [last_date + timedelta(days=i) for i in range(1, horizon + 1)]
        fallback = pd.DataFrame({"date": future_dates, "forecast": [last_val] * horizon})
        return fallback, float("nan"), float("nan")
    
    X = train[feat_cols].astype(float)
    y = train["target"].astype(float)
    
    model = LGBMRegressor(n_estimators=400, random_state=42, verbose=-1)
    model.fit(X, y)
    
    y_pred_train = model.predict(X)
    mape, rmse = evaluate(y, y_pred_train)
    
    # Recursive forecasting
    current = temp.iloc[-1:].copy().reset_index(drop=True)
    future_rows = []
    
    for i in range(horizon):
        feats = current[feat_cols].astype(float)
        pred = float(model.predict(feats)[0])
        next_date = current["date"].iloc[0] + timedelta(days=1)
        
        future_rows.append({"date": next_date, "forecast": pred})
        
        new_row = current.copy()
        new_row["date"] = pd.to_datetime([next_date])
        new_row["prev_day_net"] = [pred]
        new_row["rolling_7_mean"] = [(current["rolling_7_mean"].iloc[0] * 6 + pred) / 7]
        new_row["rolling_30_mean"] = [(current["rolling_30_mean"].iloc[0] * 29 + pred) / 30]
        new_row["lag7_mean"] = [(current["lag7_mean"].iloc[0] * 6 + pred) / 7]
        new_row["dayofweek"] = [next_date.dayofweek]
        new_row["is_weekend"] = [1 if next_date.dayofweek in (5, 6) else 0]
        new_row["month"] = [next_date.month]
        new_row["is_month_end"] = [int(pd.to_datetime(next_date).is_month_end)]
        current = new_row
    
    return pd.DataFrame(future_rows), mape, rmse


async def forecast_category(user_id: str, cat: str, db: DBConnector, horizon=14, mape_threshold=30):
    """Forecast single category"""
    df = load_category_df(user_id, cat)
    if df is None:
        return None
    
    fc_lgb, l_mape, l_rmse = run_lgb(df, horizon)
    
    best = "lgb"
    best_mape = l_mape
    stable = bool(best_mape <= mape_threshold) if not np.isnan(best_mape) else False
    
    # Prepare forecasts
    forecasts = [
        {
            "date": str(pd.to_datetime(r["date"]).date()),
            "amount": float(r["forecast"]),
            "model": "lgb",
            "confidence": 0.8 if stable else 0.6
        }
        for _, r in fc_lgb.iterrows()
    ]
    
    # Save to database
    await db.save_expense_forecasts(user_id, cat, forecasts)
    
    print(f"  ✓ {cat.upper()}: MAPE={l_mape:.2f}% | Stable={stable}")
    
    return forecasts


async def run_expense_forecast(user_id: str, db: DBConnector, horizon=14):
    """Run expense forecast for all categories"""
    print(f"\n💸 Running expense forecast for {user_id}")
    
    cats = ["fuel", "food", "rent", "phone", "misc"]
    all_forecasts = {}
    
    for cat in cats:
        result = await forecast_category(user_id, cat, db, horizon=horizon)
        if result:
            all_forecasts[cat] = result
    
    print(f"✅ Expense forecasts complete")
    return all_forecasts