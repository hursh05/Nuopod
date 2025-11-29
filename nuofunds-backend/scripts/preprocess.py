import os
import pandas as pd
import numpy as np
import re
from pathlib import Path
from scripts.db_connector import DBConnector

# Use your original preprocessing logic
PROCESSED_DIR = "data/processed"
EXPENSE_DIR = os.path.join(PROCESSED_DIR, "expenses")
FEATURES_INCOME_DIR = os.path.join("data", "features", "income")

def ensure_dir(path):
    if path and not os.path.exists(path):
        os.makedirs(path, exist_ok=True)

def normalize_narration(s):
    if pd.isna(s):
        return ""
    s = str(s).lower()
    s = re.sub(r"[^a-z0-9 @\-/]", " ", s)
    return " ".join(s.split())

# Your original categorization logic
MERCHANT_KEYWORDS = {
    "fuel": ["hpcl", "bpcl", "ioc", "indianoil", "petrol", "diesel", "fuel"],
    "food": ["zomato", "swiggy", "restaurant", "hotel", "dining", "food", "dominos"],
    "shopping": ["amazon", "flipkart", "myntra", "store", "bazaar", "mall"],
    "travel": ["ola", "uber", "rapido", "irctc", "meru"],
    "phone": ["jio", "airtel", "vi", "vodafone", "recharge"],
    "rent": ["rent", "lease", "emi", "mortgage"],
}

def categorize_expense(narr, amount):
    narr = narr.lower()
    
    for cat, keys in MERCHANT_KEYWORDS.items():
        for k in keys:
            if k in narr:
                return cat
    
    if "atm" in narr or "cash" in narr:
        return "cash"
    
    if "upi" in narr and amount <= 250:
        return "food"
    
    return "misc"

def winsorize(s, pct=0.99):
    if s.empty:
        return s
    low = s.quantile(1 - pct)
    high = s.quantile(pct)
    return s.clip(lower=low, upper=high)

def add_rolling_features(df):
    df = df.sort_values("date").reset_index(drop=True)
    
    df["rolling_7_mean"] = df["net_amt"].rolling(7, min_periods=1).mean()
    df["rolling_30_mean"] = df["net_amt"].rolling(30, min_periods=1).mean()
    df["rolling_7_std"] = df["net_amt"].rolling(7, min_periods=1).std().fillna(0)
    df["rolling_30_std"] = df["net_amt"].rolling(30, min_periods=1).std().fillna(0)
    df["prev_day_net"] = df["net_amt"].shift(1).fillna(0)
    df["lag7_mean"] = df["net_amt"].shift(7).rolling(7, min_periods=1).mean().fillna(0)
    
    df["dayofweek"] = df["date"].dt.dayofweek
    df["is_weekend"] = df["dayofweek"].isin([5, 6]).astype(int)
    df["month"] = df["date"].dt.month
    df["is_month_end"] = df["date"].dt.is_month_end.astype(int)
    
    return df


async def preprocess_from_db(user_id: str, db: DBConnector):
    """
    Preprocess transactions from database
    Modified version of your csv_preprocess.py
    """
    print(f"📥 Preprocessing data for user {user_id}")
    
    # Load from DB instead of CSV
    df = await db.get_user_transactions(user_id)
    
    if df.empty:
        print("❌ No data to process")
        return None
    
    # Use existing classification from DB or classify
    if 'isIncome' not in df.columns or df['isIncome'].isna().all():
        # Apply your original income detection
        income_keywords = ["payout", "settlement", "earning", "bonus", "incentive", "salary"]
        df["is_income"] = df["narration"].apply(
            lambda x: 1 if any(k in str(x).lower() for k in income_keywords) else 0
        )
    else:
        df["is_income"] = df["isIncome"].astype(int)
    
    # Signed amount
    df["signed"] = df.apply(
        lambda r: r["amount"] if r["is_income"] == 1 else -r["amount"], 
        axis=1
    )
    
    # DAILY AGGREGATION FOR INCOME
    daily = df.groupby(df["date"].dt.date).agg(
        net_amt=("signed", "sum"),
        tx_count=("signed", "count"),
        total_income=("amount", lambda x: x[df.loc[x.index, 'is_income'] == 1].sum()),
        total_expense=("amount", lambda x: x[df.loc[x.index, 'is_income'] == 0].sum()),
        balance=("balance", "last")
    ).reset_index()
    
    daily["date"] = pd.to_datetime(daily["date"])
    daily["net_amt"] = winsorize(daily["net_amt"])
    
    daily = add_rolling_features(daily)
    
    # Save features
    ensure_dir(PROCESSED_DIR)
    ensure_dir(FEATURES_INCOME_DIR)
    
    income_out = os.path.join(PROCESSED_DIR, f"{user_id}_features_income.csv")
    daily.to_csv(income_out, index=False)
    
    # Training snapshot
    ts = daily.rename(columns={"net_amt": "amount"})
    ts["is_income"] = (ts["amount"] > 0).astype(int)
    
    train_file = os.path.join(FEATURES_INCOME_DIR, f"{user_id}_training_snapshot.csv")
    ts.to_csv(train_file, index=False)
    
    # Save to database
    await db.save_daily_features(user_id, daily)
    
    # EXPENSE FEATURES (your original logic)
    ensure_dir(EXPENSE_DIR)
    
    df["expense_category"] = df.apply(
        lambda r: categorize_expense(r["narration"], r["amount"]), 
        axis=1
    )
    df["expense_amt"] = df.apply(
        lambda r: r["amount"] if r["is_income"] == 0 else 0, 
        axis=1
    )
    
    categories = ["food", "fuel", "travel", "shopping", "phone", "rent", "cash", "misc"]
    
    for cat in categories:
        sub = df[df["expense_category"] == cat]
        out_file = os.path.join(EXPENSE_DIR, f"{user_id}_{cat}_features.csv")
        
        if sub.empty:
            pd.DataFrame(columns=["date", "net_amt"]).to_csv(out_file, index=False)
            continue
        
        d = sub.groupby(sub["date"].dt.date).agg(
            net_amt=("expense_amt", "sum"),
            tx_count=("expense_amt", "count"),
        ).reset_index()
        
        d["date"] = pd.to_datetime(d["date"])
        d["net_amt"] = winsorize(d["net_amt"])
        d = add_rolling_features(d)
        
        d.to_csv(out_file, index=False)
        print(f"  ✓ Saved {cat} → {out_file}")
    
    print("🎉 Preprocessing complete")
    
    return {
        "income_features": income_out,
        "training_snapshot": train_file,
        "expense_features_path": EXPENSE_DIR,
    }