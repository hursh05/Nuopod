# # import os
# # import asyncpg
# # import pandas as pd
# # from typing import List, Dict, Optional
# # from dotenv import load_dotenv

# # load_dotenv()

# # DATABASE_URL = os.getenv("DATABASE_URL")


# # class DBConnector:
# #     """Database connection manager"""
    
# #     def __init__(self):
# #         self.pool = None
    
# #     async def connect(self):
# #         """Initialize connection pool"""
# #         self.pool = await asyncpg.create_pool(DATABASE_URL, min_size=2, max_size=10)
# #         print("✅ Database connected")
    
# #     async def close(self):
# #         """Close connection pool"""
# #         if self.pool:
# #             await self.pool.close()
# #             print("🔌 Database disconnected")
    
# #     async def get_user_transactions(self, user_id: str) -> pd.DataFrame:
# #         """
# #         Fetch all transactions for a user from database
# #         Returns DataFrame similar to CSV structure
# #         """
# #         async with self.pool.acquire() as conn:
# #             rows = await conn.fetch("""
# #                 SELECT 
# #                     t."id",
# #                     t."userId",
# #                     t."date",
# #                     t."amount",
# #                     t."type",
# #                     t."mode",
# #                     t."narration",
# #                     t."reference",
# #                     t."balance",
# #                     t."txnId",
# #                     tc."category",
# #                     tc."isIncome"
# #                 FROM "Transaction" t
# #                 LEFT JOIN "TransactionClassification" tc 
# #                     ON t."id" = tc."transactionId"
# #                 WHERE t."userId" = $1
# #                 ORDER BY t."date"
# #             """, user_id)
        
# #         if not rows:
# #             return pd.DataFrame()
        
# #         df = pd.DataFrame([dict(r) for r in rows])
        
# #         # Convert to format expected by original pipeline
# #         df['date'] = pd.to_datetime(df['date'])
# #         df['amount'] = df['amount'].astype(float)
        
# #         # Map to your original column names if needed
# #         df['Date'] = df['date']  # Compatibility
# #         df['Amount'] = df['amount']
# #         df['Narration'] = df['narration']
        
# #         return df
    
# #     async def save_daily_features(self, user_id: str, features_df: pd.DataFrame):
# #         """Save processed features to DailyFeatures table"""
# #         async with self.pool.acquire() as conn:
# #             for _, row in features_df.iterrows():
# #                 await conn.execute("""
# #                     INSERT INTO "DailyFeatures" (
# #                         "userId", "date", 
# #                         "totalIncome", "totalExpense", "netAmount",
# #                         "transactionCount", "closingBalance",
# #                         "rolling7Mean", "rolling30Mean", "rolling7Std",
# #                         "dayOfWeek", "isWeekend", "month"
# #                     ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
# #                     ON CONFLICT ("userId", "date") DO UPDATE SET
# #                         "totalIncome" = EXCLUDED."totalIncome",
# #                         "totalExpense" = EXCLUDED."totalExpense",
# #                         "netAmount" = EXCLUDED."netAmount",
# #                         "updatedAt" = CURRENT_TIMESTAMP
# #                 """,
# #                     user_id,
# #                     row['date'].date(),
# #                     float(row.get('total_income', 0)),
# #                     float(row.get('total_expense', 0)),
# #                     float(row.get('net_amt', 0)),
# #                     int(row.get('tx_count', 0)),
# #                     float(row.get('balance', 0)),
# #                     float(row.get('rolling_7_mean', 0)),
# #                     float(row.get('rolling_30_mean', 0)),
# #                     float(row.get('rolling_7_std', 0)),
# #                     int(row.get('dayofweek', 0)),
# #                     bool(row.get('is_weekend', False)),
# #                     int(row.get('month', 1))
# #                 )
        
# #         print(f"✅ Saved {len(features_df)} daily features to DB")
    
# #     async def save_income_forecasts(self, user_id: str, forecasts: List[Dict]):
# #         """Save income forecasts to database"""
# #         generated_at = pd.Timestamp.now()
        
# #         async with self.pool.acquire() as conn:
# #             for fc in forecasts:
# #                 await conn.execute("""
# #                     INSERT INTO "IncomeForecast" (
# #                         "userId", "forecastDate", "predictedIncome",
# #                         "confidence", "modelUsed", "mape", "generatedAt"
# #                     ) VALUES ($1, $2, $3, $4, $5, $6, $7)
# #                 """,
# #                     user_id,
# #                     pd.to_datetime(fc['date']).date(),
# #                     float(fc['amount']),
# #                     float(fc.get('confidence', 0.8)),
# #                     fc.get('model', 'lgb'),
# #                     float(fc.get('mape', 0)),
# #                     generated_at
# #                 )
        
# #         print(f"✅ Saved {len(forecasts)} income forecasts to DB")
    
# #     async def save_expense_forecasts(self, user_id: str, category: str, forecasts: List[Dict]):
# #         """Save expense forecasts to database"""
# #         generated_at = pd.Timestamp.now()
        
# #         async with self.pool.acquire() as conn:
# #             for fc in forecasts:
# #                 await conn.execute("""
# #                     INSERT INTO "ExpenseForecast" (
# #                         "userId", "forecastDate", "category",
# #                         "predictedExpense", "confidence", "modelUsed", "generatedAt"
# #                     ) VALUES ($1, $2, $3, $4, $5, $6, $7)
# #                 """,
# #                     user_id,
# #                     pd.to_datetime(fc['date']).date(),
# #                     category,
# #                     float(fc['amount']),
# #                     float(fc.get('confidence', 0.8)),
# #                     fc.get('model', 'lgb'),
# #                     generated_at
# #                 )
        
# #         print(f"✅ Saved {len(forecasts)} {category} expense forecasts to DB")
    
#     # async def save_cashflow_forecasts(self, user_id: str, forecasts: List[Dict]):
#     #     """Save cashflow/shortfall forecasts to database"""
#     #     generated_at = pd.Timestamp.now()
        
#     #     async with self.pool.acquire() as conn:
#     #         for fc in forecasts:
#     #             shortfall = fc['income'] - fc['expense']
                
#     #             await conn.execute("""
#     #                 INSERT INTO "CashflowForecast" (
#     #                     "userId", "forecastDate",
#     #                     "predictedIncome", "predictedExpense", "predictedShortfall",
#     #                     "riskLevel", "isDeficit", "generatedAt"
#     #                 ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
#     #             """,
#     #                 user_id,
#     #                 pd.to_datetime(fc['date']).date(),
#     #                 float(fc['income']),
#     #                 float(fc['expense']),
#     #                 float(shortfall),
#     #                 'high' if shortfall < 0 else 'low',
#     #                 shortfall < 0,
#     #                 generated_at
#     #             )
        
#     #     print(f"✅ Saved {len(forecasts)} cashflow forecasts to DB")
    
# #     async def get_all_user_ids(self) -> List[str]:
# #         """Get all user IDs from database"""
# #         async with self.pool.acquire() as conn:
# #             rows = await conn.fetch('SELECT "id" FROM "Customer"')
# #             return [row['id'] for row in rows]







# import os
# import asyncpg
# import pandas as pd
# from typing import List, Dict
# from dotenv import load_dotenv

# load_dotenv()

# DATABASE_URL = os.getenv("DATABASE_URL")


# class DBConnector:
#     """Database connection manager"""

#     def __init__(self):
#         self.pool = None

#     async def connect(self):
#         """Initialize connection pool"""
#         self.pool = await asyncpg.create_pool(DATABASE_URL, min_size=2, max_size=10)
#         print("✅ Database connected")

#     async def close(self):
#         """Close connection pool"""
#         if self.pool:
#             await self.pool.close()
#             print("🔌 Database disconnected")

#     # ============================================================
#     # 1️⃣ FETCH USER TRANSACTIONS
#     # ============================================================

#     async def get_user_transactions(self, user_id: str) -> pd.DataFrame:
#         """Fetch all transactions for a user"""

#         async with self.pool.acquire() as conn:
#             rows = await conn.fetch("""
#                 SELECT 
#                     t."id",
#                     t."userId",
#                     t."date",
#                     t."amount",
#                     t."type",
#                     t."mode",
#                     t."narration",
#                     t."reference",
#                     t."balance",
#                     t."txnId",
#                     tc."category",
#                     tc."isIncome"
#                 FROM "Transaction" t
#                 LEFT JOIN "TransactionClassification" tc 
#                     ON t."id" = tc."transactionId"
#                 WHERE t."userId" = $1
#                 ORDER BY t."date"
#             """, user_id)

#         if not rows:
#             return pd.DataFrame()

#         df = pd.DataFrame([dict(r) for r in rows])

#         df['date'] = pd.to_datetime(df['date'])
#         df['amount'] = df['amount'].astype(float)

#         # Compatibility with your previous CSV-based preprocess
#         df['Date'] = df['date']
#         df['Amount'] = df['amount']
#         df['Narration'] = df['narration']

#         return df

#     # ============================================================
#     # 2️⃣ SAVE DAILY FEATURES (UPSERT FIXED)
#     # ============================================================

#     async def save_daily_features(self, user_id: str, features_df: pd.DataFrame):
#         """Save processed features to DailyFeatures table"""

#         async with self.pool.acquire() as conn:
#             for _, row in features_df.iterrows():
#                 await conn.execute("""
#                     INSERT INTO "DailyFeatures" (
#                         "userId", "date",
#                         "totalIncome", "totalExpense", "netAmount",
#                         "transactionCount", "closingBalance",
#                         "rolling7Mean", "rolling30Mean", "rolling7Std",
#                         "dayOfWeek", "isWeekend", "month"
#                     ) 
#                     VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
#                     ON CONFLICT ("userId","date")
#                     DO UPDATE SET
#                         "totalIncome" = EXCLUDED."totalIncome",
#                         "totalExpense" = EXCLUDED."totalExpense",
#                         "netAmount" = EXCLUDED."netAmount",
#                         "transactionCount" = EXCLUDED."transactionCount",
#                         "closingBalance" = EXCLUDED."closingBalance",
#                         "rolling7Mean" = EXCLUDED."rolling7Mean",
#                         "rolling30Mean" = EXCLUDED."rolling30Mean",
#                         "rolling7Std" = EXCLUDED."rolling7Std",
#                         "dayOfWeek" = EXCLUDED."dayOfWeek",
#                         "isWeekend" = EXCLUDED."isWeekend",
#                         "month" = EXCLUDED."month",
#                         "updatedAt" = CURRENT_TIMESTAMP
#                 """,
#                     user_id,
#                     row['date'].date(),
#                     float(row.get('total_income', 0)),
#                     float(row.get('total_expense', 0)),
#                     float(row.get('net_amt', 0)),
#                     int(row.get('tx_count', 0)),
#                     float(row.get('balance', 0)),
#                     float(row.get('rolling_7_mean', 0)),
#                     float(row.get('rolling_30_mean', 0)),
#                     float(row.get('rolling_7_std', 0)),
#                     int(row.get('dayofweek', 0)),
#                     bool(row.get('is_weekend', False)),
#                     int(row.get('month', 1))
#                 )

#         print(f"✅ Saved {len(features_df)} daily features")

#     # ============================================================
#     # 3️⃣ SAVE INCOME FORECAST
#     # ============================================================

#     async def save_income_forecasts(self, user_id: str, forecasts: List[Dict]):
#         generated_at = pd.Timestamp.now()

#         async with self.pool.acquire() as conn:
#             for fc in forecasts:
#                 await conn.execute("""
#                     INSERT INTO "IncomeForecast" (
#                         "userId", "forecastDate", "predictedIncome",
#                         "confidence", "modelUsed", "mape", "generatedAt"
#                     )
#                     VALUES ($1, $2, $3, $4, $5, $6, $7)
#                 """,
#                     user_id,
#                     pd.to_datetime(fc["date"]).date(),
#                     float(fc["amount"]),
#                     float(fc.get("confidence", 0.8)),
#                     fc.get("model", "lgb"),
#                     float(fc.get("mape", 0)),
#                     generated_at
#                 )

#         print(f"✅ Saved {len(forecasts)} income forecasts")

#     # ============================================================
#     # 4️⃣ SAVE EXPENSE FORECAST
#     # ============================================================

#     async def save_expense_forecasts(self, user_id: str, category: str, forecasts: List[Dict]):
#         generated_at = pd.Timestamp.now()

#         async with self.pool.acquire() as conn:
#             for fc in forecasts:
#                 await conn.execute("""
#                     INSERT INTO "ExpenseForecast" (
#                         "userId", "forecastDate", "category",
#                         "predictedExpense", "confidence", "modelUsed", "generatedAt"
#                     )
#                     VALUES ($1, $2, $3, $4, $5, $6, $7)
#                 """,
#                     user_id,
#                     pd.to_datetime(fc["date"]).date(),
#                     category,
#                     float(fc["amount"]),
#                     float(fc.get("confidence", 0.8)),
#                     fc.get("model", "lgb"),
#                     generated_at
#                 )

#         print(f"✅ Saved {len(forecasts)} {category} expense forecasts")

#     # async def save_cashflow_forecasts(self, user_id: str, forecasts: List[Dict]):
#     #     """Save cashflow/shortfall forecasts to database"""
#     #     generated_at = pd.Timestamp.now()
        
#     #     async with self.pool.acquire() as conn:
#     #         for fc in forecasts:
#     #             shortfall = fc['income'] - fc['expense']
                
#     #             await conn.execute("""
#     #                 INSERT INTO "CashflowForecast" (
#     #                     "userId", "forecastDate",
#     #                     "predictedIncome", "predictedExpense", "predictedShortfall",
#     #                     "riskLevel", "isDeficit", "generatedAt"
#     #                 ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
#     #             """,
#     #                 user_id,
#     #                 pd.to_datetime(fc['date']).date(),
#     #                 float(fc['income']),
#     #                 float(fc['expense']),
#     #                 float(shortfall),
#     #                 'high' if shortfall < 0 else 'low',
#     #                 shortfall < 0,
#     #                 generated_at
#     #             )
        
#     #     print(f"✅ Saved {len(forecasts)} cashflow forecasts to DB")


#     async def save_shortfall(self, user_id: str, forecasts: List[Dict]):
#         """Save shortfall forecasts to database"""

#         generated_at = pd.Timestamp.now()

#         async with self.pool.acquire() as conn:
#             for fc in forecasts:
#                 income = float(fc["income"])
#                 expense = float(fc["expense"])
#                 shortfall = income - expense

#                 await conn.execute("""
#                     INSERT INTO "Shortfall" (
#                         "userId", "forecastDate",
#                         "predictedIncome", "predictedExpense", "predictedShortfall",
#                         "isDeficit", "riskLevel", "generatedAt"
#                     )
#                     VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
#                 """,
#                     user_id,
#                     pd.to_datetime(fc["date"]).date(),
#                     income,
#                     expense,
#                     shortfall,
#                     shortfall < 0,
#                     "high" if shortfall < 0 else "low",
#                     generated_at
#                 )

#         print(f"✅ Saved {len(forecasts)} shortfall entries")


#     # ============================================================
#     # 5️⃣ FETCH ALL CUSTOMER IDs
#     # ============================================================

#     async def get_all_user_ids(self) -> List[str]:
#         """Return all customer IDs"""

#         async with self.pool.acquire() as conn:
#             rows = await conn.fetch('SELECT "id" FROM "Customer"')
#             return [row["id"] for row in rows]




















import os
import uuid
import asyncpg
import pandas as pd
from typing import List, Dict
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")


class DBConnector:
    """Database connection manager"""

    def __init__(self):
        self.pool = None

    async def connect(self):
        """Initialize connection pool"""
        self.pool = await asyncpg.create_pool(DATABASE_URL, min_size=2, max_size=10)
        print("✅ Database connected")

    async def close(self):
        """Close connection pool"""
        if self.pool:
            await self.pool.close()
            print("🔌 Database disconnected")

    # ============================================================
    # 1️⃣ FETCH USER TRANSACTIONS
    # ============================================================

    async def get_user_transactions(self, user_id: str) -> pd.DataFrame:
        """Fetch all transactions for a user"""

        async with self.pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT 
                    t."id",
                    t."userId",
                    t."date",
                    t."amount",
                    t."type",
                    t."mode",
                    t."narration",
                    t."reference",
                    t."balance",
                    t."txnId",
                    tc."category",
                    tc."isIncome"
                FROM "Transaction" t
                LEFT JOIN "TransactionClassification" tc 
                    ON t."id" = tc."transactionId"
                WHERE t."userId" = $1
                ORDER BY t."date"
            """, user_id)

        if not rows:
            return pd.DataFrame()

        df = pd.DataFrame([dict(r) for r in rows])

        df['date'] = pd.to_datetime(df['date'])
        df['amount'] = df['amount'].astype(float)

        # Compatibility with your previous CSV-based preprocess
        df['Date'] = df['date']
        df['Amount'] = df['amount']
        df['Narration'] = df['narration']

        return df

    # ============================================================
    # 2️⃣ SAVE DAILY FEATURES (FIXED - UUID GENERATED)
    # ============================================================

    async def save_daily_features(self, user_id: str, features_df: pd.DataFrame):
        """Save processed features to DailyFeatures table"""

        async with self.pool.acquire() as conn:
            for _, row in features_df.iterrows():
                # ✅ Generate UUID for this record
                feature_id = str(uuid.uuid4())
                
                await conn.execute("""
                    INSERT INTO "DailyFeatures" (
                        "id", "userId", "date",
                        "totalIncome", "totalExpense", "netAmount",
                        "transactionCount", "closingBalance",
                        "rolling7Mean", "rolling30Mean", "rolling7Std",
                        "dayOfWeek", "isWeekend", "month"
                    ) 
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14)
                    ON CONFLICT ("userId","date")
                    DO UPDATE SET
                        "totalIncome" = EXCLUDED."totalIncome",
                        "totalExpense" = EXCLUDED."totalExpense",
                        "netAmount" = EXCLUDED."netAmount",
                        "transactionCount" = EXCLUDED."transactionCount",
                        "closingBalance" = EXCLUDED."closingBalance",
                        "rolling7Mean" = EXCLUDED."rolling7Mean",
                        "rolling30Mean" = EXCLUDED."rolling30Mean",
                        "rolling7Std" = EXCLUDED."rolling7Std",
                        "dayOfWeek" = EXCLUDED."dayOfWeek",
                        "isWeekend" = EXCLUDED."isWeekend",
                        "month" = EXCLUDED."month",
                        "updatedAt" = CURRENT_TIMESTAMP
                """,
                    feature_id,  # $1 - ✅ UUID ID
                    user_id,     # $2
                    row['date'].date(),  # $3
                    float(row.get('total_income', 0)),  # $4
                    float(row.get('total_expense', 0)),  # $5
                    float(row.get('net_amt', 0)),  # $6
                    int(row.get('tx_count', 0)),  # $7
                    float(row.get('balance', 0)),  # $8
                    float(row.get('rolling_7_mean', 0)),  # $9
                    float(row.get('rolling_30_mean', 0)),  # $10
                    float(row.get('rolling_7_std', 0)),  # $11
                    int(row.get('dayofweek', 0)),  # $12
                    bool(row.get('is_weekend', False)),  # $13
                    int(row.get('month', 1))  # $14
                )

        print(f"✅ Saved {len(features_df)} daily features")

    # ============================================================
    # 3️⃣ SAVE INCOME FORECAST (FIXED - UUID GENERATED IN PYTHON)
    # ============================================================

    async def save_income_forecasts(self, user_id: str, forecasts: List[Dict]):
        """Save income forecasts - with proper UUID generation"""
        generated_at = pd.Timestamp.now()

        async with self.pool.acquire() as conn:
            # Clean slate: delete existing forecasts for this user
            await conn.execute("""
                DELETE FROM "IncomeForecast"
                WHERE "userId" = $1 AND "forecastDate" >= CURRENT_DATE
            """, user_id)
            
            # Insert new forecasts with Python-generated UUIDs
            for fc in forecasts:
                forecast_id = str(uuid.uuid4())  # ✅ Generate UUID here!
                
                await conn.execute("""
                    INSERT INTO "IncomeForecast" (
                        "id", "userId", "forecastDate", "predictedIncome",
                        "confidence", "modelUsed", "mape", "generatedAt"
                    )
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                """,
                    forecast_id,  # Explicit ID
                    user_id,
                    pd.to_datetime(fc["date"]).date(),
                    float(fc["amount"]),
                    float(fc.get("confidence", 0.8)),
                    fc.get("model", "lgb"),
                    float(fc.get("mape", 0)),
                    generated_at
                )

        print(f"✅ Saved {len(forecasts)} income forecasts")

    # ============================================================
    # 4️⃣ SAVE EXPENSE FORECAST (FIXED - UUID GENERATED IN PYTHON)
    # ============================================================

    async def save_expense_forecasts(self, user_id: str, category: str, forecasts: List[Dict]):
        """Save expense forecasts - with proper UUID generation"""
        generated_at = pd.Timestamp.now()

        async with self.pool.acquire() as conn:
            # Clean slate: delete existing forecasts for this category
            await conn.execute("""
                DELETE FROM "ExpenseForecast"
                WHERE "userId" = $1 
                  AND "category" = $2 
                  AND "forecastDate" >= CURRENT_DATE
            """, user_id, category)
            
            # Insert new forecasts with Python-generated UUIDs
            for fc in forecasts:
                forecast_id = str(uuid.uuid4())  # ✅ Generate UUID here!
                
                await conn.execute("""
                    INSERT INTO "ExpenseForecast" (
                        "id", "userId", "forecastDate", "category",
                        "predictedExpense", "confidence", "modelUsed", "generatedAt"
                    )
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                """,
                    forecast_id,  # Explicit ID
                    user_id,
                    pd.to_datetime(fc["date"]).date(),
                    category,
                    float(fc["amount"]),
                    float(fc.get("confidence", 0.8)),
                    fc.get("model", "lgb"),
                    generated_at
                )

        print(f"✅ Saved {len(forecasts)} {category} expense forecasts")

    # ============================================================
    # 5️⃣ SAVE SHORTFALL (FIXED - UUID GENERATED IN PYTHON)
    # ============================================================

    async def save_shortfall(self, user_id: str, forecasts: List[Dict]):
        """Save shortfall forecasts - with proper UUID generation"""
        generated_at = pd.Timestamp.now()

        async with self.pool.acquire() as conn:
            # Clean slate: delete existing shortfall data
            await conn.execute("""
                DELETE FROM "Shortfall"
                WHERE "userId" = $1 AND "forecastDate" >= CURRENT_DATE
            """, user_id)
            
            # Insert new shortfall data with Python-generated UUIDs
            for fc in forecasts:
                shortfall_id = str(uuid.uuid4())  # ✅ Generate UUID here!
                
                income = float(fc["income"])
                expense = float(fc["expense"])
                shortfall = income - expense

                await conn.execute("""
                    INSERT INTO "Shortfall" (
                        "id", "userId", "forecastDate",
                        "predictedIncome", "predictedExpense", "predictedShortfall",
                        "isDeficit", "riskLevel", "generatedAt"
                    )
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                """,
                    shortfall_id,  # Explicit ID
                    user_id,
                    pd.to_datetime(fc["date"]).date(),
                    income,
                    expense,
                    shortfall,
                    shortfall < 0,
                    "high" if shortfall < 0 else "low",
                    generated_at
                )

        print(f"✅ Saved {len(forecasts)} shortfall entries")

    # ============================================================
    # 6️⃣ FETCH ALL CUSTOMER IDs
    # ============================================================

    async def get_all_user_ids(self) -> List[str]:
        """Return all customer IDs"""

        async with self.pool.acquire() as conn:
            rows = await conn.fetch('SELECT "id" FROM "Customer"')
            return [row["id"] for row in rows]