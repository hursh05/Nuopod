import os
import json
import pandas as pd
import numpy as np
from datetime import timedelta
from pathlib import Path
from lightgbm import LGBMRegressor
from sklearn.metrics import mean_absolute_percentage_error

try:
    from prophet import Prophet
    PROPHET_AVAILABLE = True
except:
    PROPHET_AVAILABLE = False

from scripts.db_connector import DBConnector

ROOT = "data/features/income"
os.makedirs(ROOT, exist_ok=True)


def evaluate(y_true, y_pred):
    y_true = np.array(y_true, dtype=float)
    y_pred = np.array(y_pred, dtype=float)
    
    if np.allclose(y_true, 0):
        return float("nan"), float(np.sqrt(np.mean((y_true - y_pred) ** 2)))
    
    denom = np.where(np.abs(y_true) < 1e-8, 1e-8, y_true)
    mape = np.mean(np.abs((y_true - y_pred) / denom)) * 100.0
    rmse = float(np.sqrt(np.mean((y_true - y_pred) ** 2)))
    return float(mape), float(rmse)


def lgb_forecast(df, horizon=14):
    """Your original LightGBM forecasting logic"""
    temp = df.copy().sort_values("date").reset_index(drop=True)
    
    feat_cols = [
        "prev_day_net", "lag7_mean", "rolling_7_mean", "rolling_30_mean",
        "dayofweek", "is_weekend", "month", "tx_count", "is_month_end"
    ]
    
    for c in feat_cols:
        if c not in temp.columns:
            temp[c] = 0.0
    
    temp["target"] = temp["amount"].shift(-1)
    train = temp.dropna(subset=["target"])
    
    if train.empty:
        last_val = float(temp["amount"].iloc[-1])
        last_date = temp["date"].max()
        future_dates = [last_date + timedelta(days=i) for i in range(1, horizon + 1)]
        return pd.DataFrame({"date": future_dates, "forecast": [last_val] * horizon}), float("nan"), float("nan")
    
    X = train[feat_cols].astype(float)
    y = train["target"].astype(float)
    
    model = LGBMRegressor(n_estimators=500, random_state=42, verbose=-1)
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


async def run_income_forecast(user_id: str, db: DBConnector, horizon=14):
    """Modified to work with DB instead of files"""
    print(f"\n💰 Running income forecast for {user_id}")
    
    train_file = os.path.join(ROOT, f"{user_id}_training_snapshot.csv")
    
    if not os.path.exists(train_file):
        print(f"❌ Training file not found: {train_file}")
        return None
    
    df = pd.read_csv(train_file, parse_dates=["date"])
    df = df.sort_values("date").reset_index(drop=True)
    
    # Run LightGBM
    fc_lgb, l_mape, l_rmse = lgb_forecast(df, horizon=horizon)
    
    selected = "lgb"
    stable = (not np.isnan(l_mape)) and (l_mape <= 25.0)
    
    # Prepare forecasts for DB
    forecasts = [
        {
            "date": str(pd.to_datetime(r["date"]).date()),
            "amount": float(r["forecast"]),
            "model": "lgb",
            "mape": l_mape,
            "confidence": 0.9 if stable else 0.7
        }
        for _, r in fc_lgb.iterrows()
    ]
    
    # Save to database
    await db.save_income_forecasts(user_id, forecasts)
    
    print(f"✅ Income forecast: {selected.upper()} | MAPE: {l_mape:.2f}% | Stable: {stable}")
    
    return forecasts