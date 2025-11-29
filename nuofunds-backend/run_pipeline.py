import os
import sys
import asyncio
import argparse
from datetime import datetime
from pathlib import Path

# Add scripts to path
sys.path.insert(0, str(Path(__file__).parent))

from scripts.db_connector import DBConnector
from scripts.data_loader import DataLoader
from scripts.preprocess import preprocess_from_db
from scripts.income_forecast import run_income_forecast
from scripts.expense_forecast import run_expense_forecast
from scripts.shortfall import run_shortfall


class NuoFundsPipeline:
    """
    Main pipeline orchestrator
    Connects your original models with database
    """
    
    def __init__(self):
        self.db = DBConnector()
        self.data_loader = None
    
    async def initialize(self):
        """Initialize database connection"""
        await self.db.connect()
        self.data_loader = DataLoader(self.db)
        print("✅ Pipeline initialized")
    
    async def close(self):
        """Close connections"""
        await self.db.close()
    
    async def run_for_user(self, user_id: str, horizon: int = 14):
        """
        Run complete pipeline for one user
        
        Steps:
        1. Load data from DB
        2. Preprocess (your csv_preprocess.py logic)
        3. Income forecast (your income.py logic)
        4. Expense forecast (your expense.py logic)
        5. Shortfall calculation (your shortfall.py logic)
        """
        print(f"\n{'='*60}")
        print(f"🚀 RUNNING PIPELINE FOR USER: {user_id}")
        print(f"{'='*60}")
        
        start_time = datetime.now()
        
        try:
            # Step 1: Preprocess data from DB
            print("\n[Step 1/4] 📊 Preprocessing...")
            result = await preprocess_from_db(user_id, self.db)
            
            if not result:
                print("❌ Preprocessing failed - insufficient data")
                return False
            
            # Step 2: Income forecasting
            print("\n[Step 2/4] 💰 Income Forecasting...")
            income_fc = await run_income_forecast(user_id, self.db, horizon=horizon)
            
            if not income_fc:
                print("❌ Income forecasting failed")
                return False
            
            # Step 3: Expense forecasting
            print("\n[Step 3/4] 💸 Expense Forecasting...")
            expense_fc = await run_expense_forecast(user_id, self.db, horizon=horizon)
            
            # Step 4: Shortfall calculation
            print("\n[Step 4/4] 📊 Shortfall Calculation...")
            shortfall = await run_shortfall(user_id, self.db)
            
            # Summary
            duration = (datetime.now() - start_time).seconds
            print(f"\n{'='*60}")
            print(f"✅ PIPELINE COMPLETED IN {duration}s")
            print(f"{'='*60}")
            
            return True
            
        except Exception as e:
            print(f"\n❌ Pipeline failed: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    async def run_for_all_users(self, horizon: int = 14):
        """Run pipeline for all users in database"""
        user_ids = await self.db.get_all_user_ids()
        
        print(f"\n📊 Found {len(user_ids)} users in database")
        
        success_count = 0
        fail_count = 0
        
        for user_id in user_ids:
            success = await self.run_for_user(user_id, horizon=horizon)
            if success:
                success_count += 1
            else:
                fail_count += 1
        
        print(f"\n{'='*60}")
        print(f"📈 FINAL SUMMARY")
        print(f"{'='*60}")
        print(f"✅ Successful: {success_count}")
        print(f"❌ Failed: {fail_count}")
        print(f"{'='*60}")


async def main():
    """CLI entry point"""
    parser = argparse.ArgumentParser(description="NuoFunds ML Pipeline")
    parser.add_argument('--user-id', type=str, help='Process specific user')
    parser.add_argument('--all', action='store_true', help='Process all users')
    parser.add_argument('--horizon', type=int, default=14, help='Forecast horizon in days')
    
    args = parser.parse_args()
    
    pipeline = NuoFundsPipeline()
    await pipeline.initialize()
    
    try:
        if args.user_id:
            # Process specific user
            await pipeline.run_for_user(args.user_id, horizon=args.horizon)
        elif args.all:
            # Process all users
            await pipeline.run_for_all_users(horizon=args.horizon)
        else:
            # No args - process all users by default
            await pipeline.run_for_all_users(horizon=args.horizon)
    
    finally:
        await pipeline.close()


if __name__ == "__main__":
    asyncio.run(main())