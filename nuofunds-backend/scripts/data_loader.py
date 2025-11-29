import os
import pandas as pd
from pathlib import Path
from scripts.db_connector import DBConnector


class DataLoader:
    """
    Load data from database instead of CSV
    Creates temporary CSV-like DataFrames for compatibility with original code
    """
    
    def __init__(self, db: DBConnector):
        self.db = db
    
    async def load_user_data_as_csv(self, user_id: str) -> pd.DataFrame:
        """
        Load user transactions from DB and format as CSV
        This maintains compatibility with your original csv_preprocess.py
        """
        df = await self.db.get_user_transactions(user_id)
        
        if df.empty:
            print(f"⚠️  No transactions found for user {user_id}")
            return df
        
        # Ensure required columns exist
        if 'date' not in df.columns and 'Date' in df.columns:
            df['date'] = df['Date']
        
        if 'amount' not in df.columns and 'Amount' in df.columns:
            df['amount'] = df['Amount']
        
        if 'narration' not in df.columns and 'Narration' in df.columns:
            df['narration'] = df['Narration']
        
        print(f"✅ Loaded {len(df)} transactions for user {user_id}")
        return df
    
    def save_to_temp_csv(self, df: pd.DataFrame, user_id: str) -> str:
        """
        Save DataFrame to temporary CSV for compatibility with original scripts
        """
        temp_dir = Path("data/temp")
        temp_dir.mkdir(parents=True, exist_ok=True)
        
        temp_file = temp_dir / f"{user_id}_transactions.csv"
        df.to_csv(temp_file, index=False)
        
        return str(temp_file)