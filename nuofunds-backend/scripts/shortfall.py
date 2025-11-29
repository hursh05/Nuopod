# import os
# import json
# import pandas as pd
# from datetime import datetime
# from scripts.db_connector import DBConnector

# async def run_shortfall(user_id: str, db: DBConnector):
#     """
#     Combine income and expense forecasts to calculate shortfall
#     Modified to work with database
#     """
#     print(f"\n📊 Calculating shortfall for {user_id}")
    
#     # Load income forecasts from DB
#     async with db.pool.acquire() as conn:
#         income_rows = await conn.fetch("""
#             SELECT "forecastDate", "predictedIncome"
#             FROM "IncomeForecast"
#             WHERE "userId" = $1
#                 AND "forecastDate" >= CURRENT_DATE
#             ORDER BY "forecastDate"
#             LIMIT 14
#         """, user_id)
        
#         # Load expense forecasts from DB
#         expense_rows = await conn.fetch("""
#             SELECT "forecastDate", "category", "predictedExpense"
#             FROM "ExpenseForecast"
#             WHERE "userId" = $1
#                 AND "forecastDate" >= CURRENT_DATE
#             ORDER BY "forecastDate", "category"
#         """, user_id)
    
#     if not income_rows:
#         print("❌ No income forecasts found")
#         return None
    
#     # Convert to DataFrames
#     df_income = pd.DataFrame([dict(r) for r in income_rows])
#     df_income.columns = ['date', 'income']
    
#     if expense_rows:
#         df_expense = pd.DataFrame([dict(r) for r in expense_rows])
#         df_expense.columns = ['date', 'category', 'expense']
        
#         # Aggregate expenses by date
#         df_total_exp = df_expense.groupby('date')['expense'].sum().reset_index()
#     else:
#         # No expense forecasts, use default
#         df_total_exp = df_income[['date']].copy()
#         df_total_exp['expense'] = 0
    
#     # Merge
#     df = pd.merge(df_income, df_total_exp, on='date', how='left')
#     df['expense'] = df['expense'].fillna(0)
#     df['shortfall'] = df['income'] - df['expense']
    
#     # Prepare for DB
#     forecasts = [
#         {
#             'date': str(row['date'].date() if hasattr(row['date'], 'date') else row['date']),
#             'income': float(row['income']),
#             'expense': float(row['expense']),
#             'shortfall': float(row['shortfall'])
#         }
#         for _, row in df.iterrows()
#     ]
    
#     # Save to database
#     await db.save_shortfall(user_id, forecasts)
    
#     print(f"✅ Shortfall calculations complete")
    
#     # Print summary
#     print("\n📈 Next 7 days forecast:")
#     for fc in forecasts[:7]:
#         emoji = "✅" if fc['shortfall'] > 0 else "⚠️"
#         print(f"{emoji} {fc['date']}: Income ₹{fc['income']:.0f} - Expense ₹{fc['expense']:.0f} = {('Surplus' if fc['shortfall'] > 0 else 'SHORTFALL')} ₹{abs(fc['shortfall']):.0f}")
    
#     return forecasts















import os
import json
import pandas as pd
from datetime import datetime
import uuid
from scripts.db_connector import DBConnector

async def run_shortfall(user_id: str, db: DBConnector):
    """
    Combine income and expense forecasts to calculate shortfall
    Modified to work with database
    """
    print(f"\n📊 Calculating shortfall for {user_id}")
    
    try:
        # Convert user_id to UUID if it's a string
        if isinstance(user_id, str):
            user_uuid = uuid.UUID(user_id)
        else:
            user_uuid = user_id
        
        # Load income forecasts from DB
        async with db.pool.acquire() as conn:
            # First check if forecasts exist
            income_count = await conn.fetchval("""
                SELECT COUNT(*) FROM "IncomeForecast"
                WHERE "userId" = $1::uuid
            """, user_uuid)
            
            print(f"  📈 Found {income_count} income forecasts in database")
            
            if income_count == 0:
                print("  ⚠️  No income forecasts found - trying without uuid cast")
                # Try without uuid cast (in case it's stored as text)
                income_count = await conn.fetchval("""
                    SELECT COUNT(*) FROM "IncomeForecast"
                    WHERE "userId" = $1
                """, user_id)
                print(f"  📈 Found {income_count} income forecasts (text match)")
            
            # Load income forecasts
            income_rows = await conn.fetch("""
                SELECT "forecastDate", "predictedIncome"
                FROM "IncomeForecast"
                WHERE "userId" = $1::uuid
                    AND "forecastDate"::date >= CURRENT_DATE
                ORDER BY "forecastDate"
                LIMIT 14
            """, user_uuid)
            
            if not income_rows:
                # Try without date filter
                print("  ⚠️  No future income forecasts, loading all recent forecasts...")
                income_rows = await conn.fetch("""
                    SELECT "forecastDate", "predictedIncome"
                    FROM "IncomeForecast"
                    WHERE "userId" = $1::uuid
                    ORDER BY "forecastDate" DESC
                    LIMIT 14
                """, user_uuid)
            
            if not income_rows:
                print("❌ No income forecasts found")
                return None
            
            print(f"  ✓ Loaded {len(income_rows)} income forecasts")
            
            # Load expense forecasts from DB
            expense_rows = await conn.fetch("""
                SELECT "forecastDate", "category", "predictedExpense"
                FROM "ExpenseForecast"
                WHERE "userId" = $1::uuid
                    AND "forecastDate"::date >= CURRENT_DATE
                ORDER BY "forecastDate", "category"
            """, user_uuid)
            
            if not expense_rows:
                # Try without date filter
                print("  ⚠️  No future expense forecasts, loading all recent forecasts...")
                expense_rows = await conn.fetch("""
                    SELECT "forecastDate", "category", "predictedExpense"
                    FROM "ExpenseForecast"
                    WHERE "userId" = $1::uuid
                    ORDER BY "forecastDate" DESC, "category"
                    LIMIT 100
                """, user_uuid)
            
            print(f"  ✓ Loaded {len(expense_rows)} expense forecasts")
        
        # Convert to DataFrames
        df_income = pd.DataFrame([dict(r) for r in income_rows])
        df_income.columns = ['date', 'income']
        
        # Ensure date is in datetime format
        df_income['date'] = pd.to_datetime(df_income['date'])
        
        if expense_rows:
            df_expense = pd.DataFrame([dict(r) for r in expense_rows])
            df_expense.columns = ['date', 'category', 'expense']
            df_expense['date'] = pd.to_datetime(df_expense['date'])
            
            # Aggregate expenses by date
            df_total_exp = df_expense.groupby('date')['expense'].sum().reset_index()
            print(f"  ✓ Aggregated expenses for {len(df_total_exp)} dates")
        else:
            # No expense forecasts, use default
            print("  ⚠️  No expense forecasts, assuming zero expenses")
            df_total_exp = df_income[['date']].copy()
            df_total_exp['expense'] = 0
        
        # Merge
        df = pd.merge(df_income, df_total_exp, on='date', how='left')
        df['expense'] = df['expense'].fillna(0)
        df['shortfall'] = df['income'] - df['expense']
        
        # Sort by date
        df = df.sort_values('date').reset_index(drop=True)
        
        # Prepare for DB
        forecasts = []
        for _, row in df.iterrows():
            try:
                forecast_date = row['date']
                if hasattr(forecast_date, 'date'):
                    forecast_date = forecast_date.date()
                
                forecasts.append({
                    'date': str(forecast_date),
                    'income': float(row['income']) if pd.notna(row['income']) else 0.0,
                    'expense': float(row['expense']) if pd.notna(row['expense']) else 0.0,
                    'shortfall': float(row['shortfall']) if pd.notna(row['shortfall']) else 0.0
                })
            except Exception as e:
                print(f"  ⚠️  Error processing row: {e}")
                continue
        
        if not forecasts:
            print("❌ No valid forecasts to save")
            return None
        
        # Save to database
        await db.save_shortfall(user_id, forecasts)
        
        print(f"✅ Saved {len(forecasts)} shortfall calculations")
        
        # Print summary
        print("\n📈 Next 7 days forecast:")
        for fc in forecasts[:7]:
            emoji = "✅" if fc['shortfall'] > 0 else "⚠️"
            status = 'Surplus' if fc['shortfall'] > 0 else 'SHORTFALL'
            print(f"{emoji} {fc['date']}: Income ₹{fc['income']:.0f} - Expense ₹{fc['expense']:.0f} = {status} ₹{abs(fc['shortfall']):.0f}")
        
        return forecasts
        
    except Exception as e:
        print(f"❌ Error in shortfall calculation: {e}")
        import traceback
        traceback.print_exc()
        return None