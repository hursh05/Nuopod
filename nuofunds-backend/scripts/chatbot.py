# import json
# from typing import List, Dict, Any, Optional, Set
# from datetime import datetime, timedelta
# from sqlalchemy import create_engine, and_, or_, desc, func, text, String
# from sqlalchemy.orm import sessionmaker, Session
# from phi.agent import Agent, AgentMemory
# from phi.model.openai import OpenAIChat
# from phi.model.google import Gemini
# from phi.storage.agent.postgres import PgAgentStorage
# from phi.memory.db.postgres import PgMemoryDb
# from phi.embedder.google import GeminiEmbedder
# from phi.knowledge.text import TextKnowledgeBase
# from phi.vectordb.pgvector import PgVector, SearchType
# from phi.utils.log import logger
# from phi.document import Document
# import os
# import hashlib
# import uuid
# from dotenv import load_dotenv

# load_dotenv()

# # OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
# GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
# OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# class FinanceChatbot:
#     def __init__(self, postgres_db_url: str, vector_db_url: str, transaction_model, 
#                  customer_model, insights_model, forecast_model, classification_model):
#         """
#         Initialize the finance chatbot with proper error handling and validation
        
#         Args:
#             postgres_db_url: PostgreSQL database URL
#             vector_db_url: PostgreSQL URL for vector storage
#             transaction_model: SQLAlchemy Transaction model
#             customer_model: SQLAlchemy Customer model
#             insights_model: SQLAlchemy UserFinancialInsights model
#             forecast_model: SQLAlchemy IncomeForecast/ExpenseForecast models
#             classification_model: SQLAlchemy TransactionClassification model
#         """
#         try:
#             self.postgres_engine = create_engine(
#                 postgres_db_url,
#                 pool_pre_ping=True,
#                 pool_recycle=3600,
#                 echo=False
#             )
#             self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.postgres_engine)
#             self.vector_db_url = vector_db_url
            
#             # Store models
#             self.Transaction = transaction_model
#             self.Customer = customer_model
#             self.UserFinancialInsights = insights_model
#             self.TransactionClassification = classification_model
            
#             self.agents = {}
#             self.knowledge_bases = {}
            
#             # Track processed transactions per user
#             self.processed_transactions = {}
            
#             # Test connections
#             self._test_database_connections()
#             logger.info("FinanceChatbot initialized successfully")
            
#         except Exception as e:
#             logger.error(f"Failed to initialize FinanceChatbot: {e}")
#             raise

#     def _test_database_connections(self):
#         """Test database connections"""
#         try:
#             with self.SessionLocal() as db:
#                 db.execute(text("SELECT 1"))
#             logger.info("PostgreSQL connection successful")
            
#         except Exception as e:
#             logger.error(f"Database connection test failed: {e}")
#             raise

#     def create_finance_tools(self, user_id: str):
#         """Create user-specific financial analysis tools"""
        
#         def get_user_transactions(
#             limit: int = 20,
#             start_date: Optional[str] = None,
#             end_date: Optional[str] = None,
#             transaction_type: Optional[str] = None,
#             category: Optional[str] = None,
#             min_amount: Optional[float] = None,
#             max_amount: Optional[float] = None
#         ) -> str:
#             """Get transactions for the current user with comprehensive filtering"""
#             try:
#                 with self.SessionLocal() as db:
#                     print("Transaction attributes:", dir(self.Transaction))
#                     print("Transaction columns:", [c.name for c in self.Transaction.__table__.columns])
#                     query = db.query(self.Transaction).filter(
#                         self.Transaction.user_id == user_id
#                     )
                    
#                     # Add filters
#                     if start_date:
#                         try:
#                             start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
#                             query = query.filter(self.Transaction.date >= start_dt)
#                         except ValueError as e:
#                             logger.warning(f"Invalid start_date format: {start_date}")
                    
#                     if end_date:
#                         try:
#                             end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
#                             query = query.filter(self.Transaction.date <= end_dt)
#                         except ValueError as e:
#                             logger.warning(f"Invalid end_date format: {end_date}")
                    
#                     if transaction_type:
#                         query = query.filter(self.Transaction.type.ilike(f"%{transaction_type}%"))
                    
#                     if min_amount:
#                         query = query.filter(self.Transaction.amount >= min_amount)
                    
#                     if max_amount:
#                         query = query.filter(self.Transaction.amount <= max_amount)
                    
#                     # Join with classification for category filtering
#                     if category:
#                         query = query.join(
#                             self.TransactionClassification,
#                             self.Transaction.id == self.TransactionClassification.transaction_id
#                         ).filter(
#                             self.TransactionClassification.category.ilike(f"%{category}%")
#                         )
                    
#                     transactions = query.order_by(desc(self.Transaction.date)).limit(limit).all()
                    
#                     results = []
#                     for txn in transactions:
#                         try:
#                             # Get classification if available
#                             classification = db.query(self.TransactionClassification).filter(
#                                 self.TransactionClassification.transaction_id == txn.id
#                             ).first()
                            
#                             results.append({
#                                 'id': getattr(txn, 'id', None),
#                                 'amount': float(getattr(txn, 'amount', 0)),
#                                 'type': getattr(txn, 'type', None),
#                                 'mode': getattr(txn, 'mode', None),
#                                 'date': txn.date.isoformat() if getattr(txn, 'date', None) else None,
#                                 'narration': getattr(txn, 'narration', None),
#                                 'balance': float(getattr(txn, 'balance', 0)) if getattr(txn, 'balance', None) else None,
#                                 'category': classification.category if classification else 'uncategorized',
#                                 'merchant': classification.merchantName if classification else None,
#                                 'is_income': classification.is_income if classification else False
#                             })
#                         except Exception as e:
#                             logger.error(f"Error processing transaction {getattr(txn, 'id', 'unknown')}: {e}")
#                             continue
                    
#                     return json.dumps({
#                         "transactions": results,
#                         "count": len(results),
#                         "total_available": query.count() if limit < 100 else "many"
#                     }, indent=2)
                    
#             except Exception as e:
#                 logger.error(f"Error fetching transactions for user {user_id}: {e}")
#                 return json.dumps({"error": f"Error fetching transactions: {str(e)}"})

#         def get_spending_by_category(
#             days: int = 30,
#             start_date: Optional[str] = None,
#             end_date: Optional[str] = None
#         ) -> str:
#             """Get spending breakdown by category"""
#             try:
#                 with self.SessionLocal() as db:
#                     # Calculate date range
#                     if start_date and end_date:
#                         start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
#                         end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
#                     else:
#                         end_dt = datetime.utcnow()
#                         start_dt = end_dt - timedelta(days=days)
                    
#                     # Query spending by category
#                     category_spending = db.query(
#                         self.TransactionClassification.category,
#                         func.sum(self.Transaction.amount).label('total'),
#                         func.count(self.Transaction.id).label('count'),
#                         func.avg(self.Transaction.amount).label('average')
#                     ).join(
#                         self.Transaction,
#                         self.TransactionClassification.transaction_id == self.Transaction.id
#                     ).filter(
#                         and_(
#                             self.Transaction.user_id == user_id,
#                             self.Transaction.date >= start_dt,
#                             self.Transaction.date <= end_dt,
#                             self.TransactionClassification.is_income == False
#                         )
#                     ).group_by(
#                         self.TransactionClassification.category
#                     ).order_by(
#                         desc('total')
#                     ).all()
                    
#                     # Calculate total spending
#                     total_spending = sum(float(cat.total) for cat in category_spending)
                    
#                     results = []
#                     for cat in category_spending:
#                         results.append({
#                             'category': cat.category,
#                             'total_spent': float(cat.total),
#                             'transaction_count': cat.count,
#                             'average_transaction': float(cat.average),
#                             'percentage_of_total': round((float(cat.total) / total_spending * 100), 2) if total_spending > 0 else 0
#                         })
                    
#                     return json.dumps({
#                         "period_days": days,
#                         "start_date": start_dt.isoformat(),
#                         "end_date": end_dt.isoformat(),
#                         "total_spending": round(total_spending, 2),
#                         "categories": results,
#                         "category_count": len(results)
#                     }, indent=2)
                    
#             except Exception as e:
#                 logger.error(f"Error getting category spending: {e}")
#                 return json.dumps({"error": f"Failed to get category spending: {str(e)}"})

#         def get_income_analysis(days: int = 30) -> str:
#             """Analyze income patterns"""
#             try:
#                 with self.SessionLocal() as db:
#                     end_dt = datetime.utcnow()
#                     start_dt = end_dt - timedelta(days=days)
                    
#                     # Get income transactions
#                     income_txns = db.query(self.Transaction).join(
#                         self.TransactionClassification,
#                         self.Transaction.id == self.TransactionClassification.transaction_id
#                     ).filter(
#                         and_(
#                             self.Transaction.user_id == user_id,
#                             self.Transaction.date >= start_dt,
#                             self.TransactionClassification.is_income == True
#                         )
#                     ).all()
                    
#                     if not income_txns:
#                         return json.dumps({
#                             "message": "No income transactions found in this period",
#                             "total_income": 0,
#                             "transaction_count": 0
#                         })
                    
#                     total_income = sum(float(txn.amount) for txn in income_txns)
#                     avg_income = total_income / len(income_txns)
                    
#                     # Get income sources
#                     income_by_source = {}
#                     for txn in income_txns:
#                         narration = getattr(txn, 'narration', 'Unknown')
#                         if narration not in income_by_source:
#                             income_by_source[narration] = {
#                                 'total': 0,
#                                 'count': 0
#                             }
#                         income_by_source[narration]['total'] += float(txn.amount)
#                         income_by_source[narration]['count'] += 1
                    
#                     sources = [
#                         {
#                             'source': source,
#                             'total': round(data['total'], 2),
#                             'count': data['count'],
#                             'percentage': round((data['total'] / total_income * 100), 2)
#                         }
#                         for source, data in sorted(
#                             income_by_source.items(),
#                             key=lambda x: x[1]['total'],
#                             reverse=True
#                         )
#                     ]
                    
#                     return json.dumps({
#                         "period_days": days,
#                         "total_income": round(total_income, 2),
#                         "transaction_count": len(income_txns),
#                         "average_income_per_transaction": round(avg_income, 2),
#                         "daily_average": round(total_income / days, 2),
#                         "income_sources": sources
#                     }, indent=2)
                    
#             except Exception as e:
#                 logger.error(f"Error analyzing income: {e}")
#                 return json.dumps({"error": f"Failed to analyze income: {str(e)}"})

#         def get_financial_insights(user_id: str) -> str:
#             """Get user's latest financial insights"""
#             try:
#                 with self.SessionLocal() as db:
#                     insights = db.query(self.UserFinancialInsights).filter(
#                         self.UserFinancialInsights.user_id == user_id
#                     ).order_by(
#                         desc(self.UserFinancialInsights.analysisDate)
#                     ).first()
                    
#                     if not insights:
#                         return json.dumps({
#                             "message": "No financial insights available yet",
#                             "recommendation": "Please ensure you have transaction data for analysis"
#                         })
                    
#                     result = {
#                         'analysis_date': insights.analysisDate.isoformat() if insights.analysisDate else None,
#                         'period_days': insights.analysisPeriodDays,
#                         'income': {
#                             'avg_daily': float(insights.avgDailyIncome) if insights.avgDailyIncome else 0,
#                             'stability': insights.incomeStability,
#                             'growth_rate': float(insights.incomeGrowthRate) if insights.incomeGrowthRate else 0
#                         },
#                         'expenses': {
#                             'avg_daily': float(insights.avgDailyExpense) if insights.avgDailyExpense else 0,
#                             'stability': insights.expenseStability,
#                             'top_category': insights.topExpenseCategory,
#                             'top_category_amount': float(insights.topExpenseCategoryAmount) if insights.topExpenseCategoryAmount else 0
#                         },
#                         'savings': {
#                             'avg_daily': float(insights.avgDailySavings) if insights.avgDailySavings else 0,
#                             'rate': float(insights.savingsRate) if insights.savingsRate else 0,
#                             'total_last_30_days': float(insights.totalSavingsLast30Days) if insights.totalSavingsLast30Days else 0,
#                             'consistency': insights.savingsConsistency
#                         },
#                         'balance': {
#                             'avg_daily': float(insights.avgDailyBalance) if insights.avgDailyBalance else 0,
#                             'lowest': float(insights.lowestBalance) if insights.lowestBalance else 0,
#                             'lowest_date': insights.lowestBalanceDate.isoformat() if insights.lowestBalanceDate else None
#                         },
#                         'risk': {
#                             'level': insights.overallRiskLevel,
#                             'score': float(insights.riskScore) if insights.riskScore else 0,
#                             'factors': insights.riskFactors or [],
#                             'cash_crunch_risk': insights.cashCrunchRisk
#                         },
#                         'strengths': insights.strengths or [],
#                         'weaknesses': insights.weaknesses or [],
#                         'predictions': {
#                             'shortfall_days': insights.predictedShortfallDays,
#                             'shortfall_amount': float(insights.predictedShortfallAmount) if insights.predictedShortfallAmount else 0,
#                             'next_low_balance_date': insights.nextLowBalanceDate.isoformat() if insights.nextLowBalanceDate else None
#                         },
#                         'recommendations': {
#                             'daily_savings': float(insights.recommendedDailySavings) if insights.recommendedDailySavings else 0,
#                             'emergency_fund': float(insights.recommendedEmergencyFund) if insights.recommendedEmergencyFund else 0
#                         },
#                         'financial_health_grade': insights.financialHealthGrade,
#                         'summary': insights.insightsSummary
#                     }
                    
#                     return json.dumps(result, indent=2)
                    
#             except Exception as e:
#                 logger.error(f"Error getting insights: {e}")
#                 return json.dumps({"error": f"Failed to get insights: {str(e)}"})

#         def search_transactions(
#             keyword: str,
#             limit: int = 10
#         ) -> str:
#             """Search transactions by keyword in narration"""
#             try:
#                 with self.SessionLocal() as db:
#                     query = db.query(self.Transaction).filter(
#                         and_(
#                             self.Transaction.user_id == user_id,
#                             self.Transaction.narration.ilike(f"%{keyword}%")
#                         )
#                     ).order_by(desc(self.Transaction.date)).limit(limit)
                    
#                     transactions = query.all()
                    
#                     results = []
#                     for txn in transactions:
#                         classification = db.query(self.TransactionClassification).filter(
#                             self.TransactionClassification.transaction_id == txn.id
#                         ).first()
                        
#                         results.append({
#                             'id': txn.id,
#                             'amount': float(txn.amount),
#                             'type': txn.type,
#                             'date': txn.date.isoformat(),
#                             'narration': txn.narration,
#                             'category': classification.category if classification else 'uncategorized'
#                         })
                    
#                     return json.dumps({
#                         "keyword": keyword,
#                         "transactions": results,
#                         "count": len(results)
#                     }, indent=2)
                    
#             except Exception as e:
#                 logger.error(f"Error searching transactions: {e}")
#                 return json.dumps({"error": f"Search failed: {str(e)}"})

#         def get_monthly_summary(month: Optional[int] = None, year: Optional[int] = None) -> str:
#             """Get monthly financial summary"""
#             try:
#                 with self.SessionLocal() as db:
#                     if not month or not year:
#                         now = datetime.utcnow()
#                         month = now.month
#                         year = now.year
                    
#                     start_date = datetime(year, month, 1)
#                     if month == 12:
#                         end_date = datetime(year + 1, 1, 1)
#                     else:
#                         end_date = datetime(year, month + 1, 1)
                    
#                     # Get all transactions for the month
#                     transactions = db.query(self.Transaction).filter(
#                         and_(
#                             self.Transaction.user_id == user_id,
#                             self.Transaction.date >= start_date,
#                             self.Transaction.date < end_date
#                         )
#                     ).all()
                    
#                     total_income = 0
#                     total_expense = 0
                    
#                     for txn in transactions:
#                         classification = db.query(self.TransactionClassification).filter(
#                             self.TransactionClassification.transaction_id == txn.id
#                         ).first()
                        
#                         if classification and classification.is_income:
#                             total_income += float(txn.amount)
#                         else:
#                             total_expense += float(txn.amount)
                    
#                     net_savings = total_income - total_expense
#                     savings_rate = (net_savings / total_income * 100) if total_income > 0 else 0
                    
#                     return json.dumps({
#                         "month": month,
#                         "year": year,
#                         "total_income": round(total_income, 2),
#                         "total_expense": round(total_expense, 2),
#                         "net_savings": round(net_savings, 2),
#                         "savings_rate": round(savings_rate, 2),
#                         "transaction_count": len(transactions)
#                     }, indent=2)
                    
#             except Exception as e:
#                 logger.error(f"Error getting monthly summary: {e}")
#                 return json.dumps({"error": f"Failed to get monthly summary: {str(e)}"})

#         return [
#             get_user_transactions,
#             get_spending_by_category,
#             get_income_analysis,
#             get_financial_insights,
#             search_transactions,
#             get_monthly_summary
#         ]

#     def _generate_content_hash(self, content: str) -> str:
#         """Generate hash of content to detect duplicates"""
#         return hashlib.sha256(content.encode('utf-8')).hexdigest()

#     def _get_processed_transactions(self, user_id: str) -> Set[str]:
#         """Get set of already processed transaction hashes for a user"""
#         if user_id not in self.processed_transactions:
#             self.processed_transactions[user_id] = set()
#         return self.processed_transactions[user_id]

#     def _mark_transaction_processed(self, user_id: str, content_hash: str):
#         """Mark a transaction as processed"""
#         if user_id not in self.processed_transactions:
#             self.processed_transactions[user_id] = set()
#         self.processed_transactions[user_id].add(content_hash)

#     def create_user_knowledge_base(self, user_id: str, force_refresh: bool = False) -> TextKnowledgeBase:
#         """Create user-specific knowledge base from financial data"""
        
#         if user_id in self.knowledge_bases and not force_refresh:
#             logger.info(f"Returning existing knowledge base for user {user_id}")
#             self._update_knowledge_base_incrementally(user_id)
#             return self.knowledge_bases[user_id]
        
#         try:
#             knowledge_base = TextKnowledgeBase(
#                 path=f"user_{user_id}_finance_knowledge",
#                 vector_db=PgVector(
#                     table_name="user_finance_knowledge",
#                     db_url=self.vector_db_url,
#                     search_type=SearchType.hybrid
#                 )
#             )
            
#             with self.SessionLocal() as db:
#                 # Get user's transactions with classifications
#                 transactions = db.query(self.Transaction).filter(
#                     self.Transaction.user_id == user_id
#                 ).order_by(desc(self.Transaction.date)).limit(500).all()
                
#                 if not transactions:
#                     logger.warning(f"No transactions found for user {user_id}")
#                     self.knowledge_bases[user_id] = knowledge_base
#                     return knowledge_base
                
#                 processed_hashes = self._get_processed_transactions(user_id)
#                 documents = []
                
#                 # Create documents from transactions (grouped by month)
#                 transactions_by_month = {}
#                 for txn in transactions:
#                     if not txn.date:
#                         continue
                    
#                     month_key = txn.date.strftime('%Y-%m')
#                     if month_key not in transactions_by_month:
#                         transactions_by_month[month_key] = []
                    
#                     classification = db.query(self.TransactionClassification).filter(
#                         self.TransactionClassification.transaction_id == txn.id
#                     ).first()
                    
#                     transactions_by_month[month_key].append({
#                         'transaction': txn,
#                         'classification': classification
#                     })
                
#                 # Create documents for each month
#                 for month_key, month_txns in transactions_by_month.items():
#                     content_parts = [f"Financial transactions for {month_key}:\n"]
                    
#                     total_income = 0
#                     total_expense = 0
                    
#                     for item in month_txns:
#                         txn = item['transaction']
#                         classification = item['classification']
                        
#                         is_income = classification.is_income if classification else False
#                         category = classification.category if classification else 'uncategorized'
                        
#                         if is_income:
#                             total_income += float(txn.amount)
#                         else:
#                             total_expense += float(txn.amount)
                        
#                         content_parts.append(
#                             f"{txn.date.strftime('%Y-%m-%d')}: {txn.type} "
#                             f"₹{txn.amount} - {category} - {txn.narration or 'No description'}"
#                         )
                    
#                     content_parts.append(f"\nMonth Summary:")
#                     content_parts.append(f"Total Income: ₹{total_income:.2f}")
#                     content_parts.append(f"Total Expenses: ₹{total_expense:.2f}")
#                     content_parts.append(f"Net Savings: ₹{(total_income - total_expense):.2f}")
                    
#                     content = "\n".join(content_parts)
#                     content_hash = self._generate_content_hash(content)
                    
#                     if content_hash not in processed_hashes:
#                         doc_id = f"user_{user_id}_month_{month_key}_{uuid.uuid4().hex[:8]}"
                        
#                         documents.append(
#                             Document(
#                                 id=doc_id,
#                                 content=content,
#                                 metadata={
#                                     'user_id': user_id,
#                                     'month': month_key,
#                                     'total_income': total_income,
#                                     'total_expense': total_expense,
#                                     'transaction_count': len(month_txns),
#                                     'content_hash': content_hash
#                                 }
#                             )
#                         )
#                         self._mark_transaction_processed(user_id, content_hash)
                
#                 # Add financial insights as a document
#                 insights = db.query(self.UserFinancialInsights).filter(
#                     self.UserFinancialInsights.user_id == user_id
#                 ).order_by(desc(self.UserFinancialInsights.analysisDate)).first()
                
#                 if insights:
#                     insights_content = f"""
#                     Financial Insights Summary:

#                     Income Analysis:
#                     - Average Daily Income: ₹{insights.avgDailyIncome or 0:.2f}
#                     - Income Stability: {insights.incomeStability or 'Unknown'}
#                     - Income Growth Rate: {insights.incomeGrowthRate or 0:.2f}%

#                     Expense Analysis:
#                     - Average Daily Expense: ₹{insights.avgDailyExpense or 0:.2f}
#                     - Top Expense Category: {insights.topExpenseCategory or 'Unknown'}
#                     - Top Category Spending: ₹{insights.topExpenseCategoryAmount or 0:.2f}

#                     Savings:
#                     - Average Daily Savings: ₹{insights.avgDailySavings or 0:.2f}
#                     - Savings Rate: {insights.savingsRate or 0:.2f}%
#                     - Total Savings (Last 30 Days): ₹{insights.totalSavingsLast30Days or 0:.2f}

#                     Risk Assessment:
#                     - Overall Risk Level: {insights.overallRiskLevel or 'Unknown'}
#                     - Risk Score: {insights.riskScore or 0:.2f}
#                     - Financial Health Grade: {insights.financialHealthGrade or 'N/A'}

#                     Strengths: {', '.join(insights.strengths or [])}
#                     Weaknesses: {', '.join(insights.weaknesses or [])}

#                     Summary: {insights.insightsSummary or 'No summary available'}
#                     """
                    
#                     insights_hash = self._generate_content_hash(insights_content)
#                     if insights_hash not in processed_hashes:
#                         documents.append(
#                             Document(
#                                 id=f"user_{user_id}_insights_{uuid.uuid4().hex[:8]}",
#                                 content=insights_content,
#                                 metadata={
#                                     'user_id': user_id,
#                                     'type': 'insights',
#                                     'analysis_date': insights.analysisDate.isoformat(),
#                                     'content_hash': insights_hash
#                                 }
#                             )
#                         )
#                         self._mark_transaction_processed(user_id, insights_hash)
                
#                 logger.info(f"Prepared {len(documents)} documents for user {user_id}")
                
#                 # Load documents in batches
#                 if documents:
#                     batch_size = 5
#                     for i in range(0, len(documents), batch_size):
#                         batch = documents[i:i + batch_size]
#                         try:
#                             knowledge_base.load_documents(batch, upsert=True)
#                             logger.info(f"Loaded batch {i//batch_size + 1}")
#                         except Exception as e:
#                             logger.error(f"Error loading batch: {e}")
                
#                 self.knowledge_bases[user_id] = knowledge_base
#                 logger.info(f"Successfully created knowledge base for user {user_id}")
#                 return knowledge_base
                
#         except Exception as e:
#             logger.error(f"Error creating knowledge base for user {user_id}: {e}")
#             basic_kb = TextKnowledgeBase(
#                 path=f"user_{user_id}_finance_basic",
#                 vector_db=PgVector(
#                     table_name="user_finance_knowledge",
#                     db_url=self.vector_db_url,
#                     search_type=SearchType.hybrid,
#                 )
#             )
#             self.knowledge_bases[user_id] = basic_kb
#             return basic_kb

#     def _update_knowledge_base_incrementally(self, user_id: str):
#         """Update existing knowledge base with new transactions"""
#         try:
#             if user_id not in self.knowledge_bases:
#                 return
            
#             knowledge_base = self.knowledge_bases[user_id]
#             processed_hashes = self._get_processed_transactions(user_id)
            
#             with self.SessionLocal() as db:
#                 # Get recent transactions (last 7 days)
#                 recent_date = datetime.utcnow() - timedelta(days=7)
#                 recent_txns = db.query(self.Transaction).filter(
#                     and_(
#                         self.Transaction.user_id == user_id,
#                         self.Transaction.date >= recent_date
#                     )
#                 ).all()
                
#                 if recent_txns:
#                     # Process new transactions
#                     month_key = datetime.utcnow().strftime('%Y-%m')
#                     content_parts = [f"Recent transactions for {month_key}:\n"]
                    
#                     for txn in recent_txns:
#                         classification = db.query(self.TransactionClassification).filter(
#                             self.TransactionClassification.transaction_id == txn.id
#                         ).first()
                        
#                         category = classification.category if classification else 'uncategorized'
#                         content_parts.append(
#                             f"{txn.date.strftime('%Y-%m-%d')}: {txn.type} "
#                             f"₹{txn.amount} - {category} - {txn.narration or 'No description'}"
#                         )
                    
#                     content = "\n".join(content_parts)
#                     content_hash = self._generate_content_hash(content)
                    
#                     if content_hash not in processed_hashes:
#                         doc = Document(
#                             id=f"user_{user_id}_recent_{uuid.uuid4().hex[:8]}",
#                             content=content,
#                             metadata={
#                                 'user_id': user_id,
#                                 'month': month_key,
#                                 'type': 'recent',
#                                 'content_hash': content_hash
#                             }
#                         )
#                         knowledge_base.load_documents([doc], upsert=True)
#                         logger.info(f"Added recent transactions document for user {user_id}")
                
#         except Exception as e:
#             logger.error(f"Error updating knowledge base incrementally for user {user_id}: {e}")

#     def get_or_create_agent(self, user_id: str) -> Agent:
#         """Get or create user-specific agent with enhanced configuration"""
        
#         if user_id not in self.agents:
#             try:
#                 logger.info(f"Creating new agent for user {user_id}")
                
#                 # Create user-specific tools
#                 tools = self.create_finance_tools(user_id)
                
#                 # Create user-specific knowledge base
#                 knowledge_base = self.create_user_knowledge_base(user_id)
                
#                 # Create memory configuration
#                 memory_db = PgMemoryDb(
#                     table_name="agent_memory",
#                     db_url=self.vector_db_url,
#                     schema="ai"
#                 )
                
#                 # Create agent storage
#                 agent_storage = PgAgentStorage(
#                     table_name="agent_sessions", 
#                     db_url=self.vector_db_url,
#                     schema="ai"
#                 )
                
#                 # Create agent with comprehensive configuration
#                 agent = Agent(
#                     model=OpenAIChat(
#                     id="gpt-4o",  # or "gpt-4o-mini" for cheaper/faster
#                     api_key=OPENAI_API_KEY
#                 ),
                    
#                     # User-specific storage and memory
#                     storage=agent_storage,
#                     user_id=user_id,
                    
#                     # Enhanced memory configuration
#                     memory=AgentMemory(
#                         db=memory_db,
#                         create_user_memories=True,
#                         create_session_summary=True,
#                         update_user_memories_after_run=True,
#                         update_session_summary_after_run=True
#                     ),
                    
#                     # Memory and history settings
#                     add_history_to_messages=True,
#                     num_history_responses=5,
#                     create_memories=True,
#                     update_memories=True,
#                     read_chat_history=True,
                    
#                     # Knowledge base configuration
#                     knowledge=knowledge_base,
#                     search_knowledge=True,
                    
#                     # Tools for database access
#                     tools=tools,
#                     show_tool_calls=False,
                    
#                     # Agent identification
#                     name=f"FinanceAssistant_{user_id}",
                    
#                     # Enhanced system prompt
#                     instructions=f"""
#                     You are an intelligent personal finance assistant for user {user_id}. You have access to their financial data, transactions, and insights.

#                     SECURITY & ACCESS CONTROL:
#                     - You can ONLY access data for user {user_id}
#                     - Never share information about other users
#                     - All database queries are automatically filtered for this user
#                     - If asked about other users, politely decline

#                     CAPABILITIES:
#                     1. **Transaction Analysis**: View and analyze spending patterns, income sources, and transaction history
#                     2. **Category Insights**: Break down expenses by category with percentages and trends
#                     3. **Income Analysis**: Track income sources, stability, and growth patterns
#                     4. **Financial Health**: Access comprehensive financial insights including risk assessment
#                     5. **Savings Analysis**: Monitor savings rate, consistency, and recommendations
#                     6. **Search & Filter**: Find specific transactions by keyword, date, category, or amount
#                     7. **Monthly Summaries**: Get detailed monthly financial overviews

#                     FINANCIAL DATA STRUCTURE:
#                     - Transactions: amount, type (credit/debit), date, narration, category, merchant
#                     - Classifications: category, merchant name, income vs expense
#                     - Insights: income/expense stability, savings rate, risk level, financial health grade
#                     - All amounts in INR (₹)

#                     RESPONSE GUIDELINES:
#                     - Be conversational, supportive, and financially savvy
#                     - Provide actionable financial advice based on data
#                     - Use data to give personalized insights
#                     - Explain financial concepts clearly
#                     - Highlight both strengths and areas for improvement
#                     - Suggest specific actions to improve financial health
#                     - When showing amounts, format with ₹ symbol
#                     - Remember user preferences and context from previous conversations

#                     FINANCIAL ADVICE PRINCIPLES:
#                     - Encourage healthy saving habits
#                     - Point out unusual spending patterns
#                     - Celebrate financial wins (savings, reduced expenses)
#                     - Warn about potential risks (low balance, high spending)
#                     - Suggest budget optimizations based on category spending
#                     - Help identify unnecessary expenses

#                     EXAMPLE INTERACTIONS:
#                     - "Show me my spending this month"
#                     - "What's my biggest expense category?"
#                     - "How much did I save last month?"
#                     - "Find all transactions to Amazon"
#                     - "What's my financial health score?"
#                     - "Where can I cut my expenses?"
#                     - "Show me my income sources"

#                     Always be proactive in helping users improve their financial health and make better money decisions.
#                     Use the currency symbol ₹ when displaying amounts.
#                     """,
                    
#                     # Additional configurations
#                     markdown=True,
#                     debug_mode=False,
#                     add_datetime_to_instructions=True,
#                     prevent_prompt_injection=True,
#                     limit_tool_access=False,
#                     reasoning=False,
#                 )
                
#                 # Initialize agent tables
#                 try:
#                     agent.create_memories = True
#                     agent.update_memories = True
#                     logger.info(f"Agent tables initialized for user {user_id}")
#                 except Exception as table_error:
#                     logger.warning(f"Error initializing agent tables: {table_error}")
                
#                 self.agents[user_id] = agent
#                 logger.info(f"Successfully created agent for user {user_id}")
                
#             except Exception as e:
#                 logger.error(f"Error creating agent for user {user_id}: {e}")
#                 raise
        
#         return self.agents[user_id]

#     def chat(self, user_id: str, message: str, session_id: Optional[str] = None) -> Dict[str, Any]:
#         """Handle user chat message with enhanced error handling"""
        
#         try:
#             # Validate input
#             if not user_id or not message:
#                 return {
#                     "response": "Please provide a valid user ID and message.",
#                     "success": False,
#                     "error": "Invalid input parameters"
#                 }
            
#             logger.info(f"Processing chat for user {user_id}, session: {session_id}")
            
#             # Get or create user-specific agent
#             agent = self.get_or_create_agent(user_id)
            
#             # Set session ID if provided
#             if session_id:
#                 agent.session_id = session_id
#             elif not hasattr(agent, 'session_id') or not agent.session_id:
#                 agent.session_id = f"session_{user_id}_{uuid.uuid4().hex[:8]}"
            
#             logger.info(f"Using session ID: {agent.session_id}")
            
#             # Process the message
#             try:
#                 response = agent.run(message)
#             except Exception as agent_error:
#                 logger.error(f"Error running agent for user {user_id}: {agent_error}")
#                 return {
#                     "response": "I encountered an error while processing your request. Please try again.",
#                     "success": False,
#                     "error": f"Agent error: {str(agent_error)}",
#                     "user_id": user_id,
#                     "session_id": agent.session_id,
#                     "timestamp": datetime.utcnow().isoformat()
#                 }
            
#             # Extract response content
#             response_content = response.content if hasattr(response, 'content') else str(response)
            
#             logger.info(f"Generated response for user {user_id}")
            
#             # Return structured response
#             return {
#                 "response": response_content,
#                 "success": True,
#                 "session_id": agent.session_id,
#                 "user_id": user_id,
#                 "timestamp": datetime.utcnow().isoformat(),
#                 "message_length": len(message),
#                 "response_length": len(response_content)
#             }
            
#         except Exception as e:
#             logger.error(f"Error processing chat for user {user_id}: {e}")
#             return {
#                 "response": "I encountered an error while processing your request. Please try again or contact support.",
#                 "success": False,
#                 "error": str(e),
#                 "user_id": user_id,
#                 "session_id": session_id,
#                 "timestamp": datetime.utcnow().isoformat()
#             }

#     def get_user_sessions(self, user_id: str) -> List[str]:
#         """Get all sessions for a user"""
#         try:
#             agent = self.get_or_create_agent(user_id)
#             if hasattr(agent.storage, 'get_all_session_ids'):
#                 return agent.storage.get_all_session_ids(user_id)
#             else:
#                 logger.warning(f"Storage doesn't support get_all_session_ids for user {user_id}")
#                 return []
#         except Exception as e:
#             logger.error(f"Error getting user sessions for {user_id}: {e}")
#             return []

#     def refresh_user_knowledge(self, user_id: str, force_refresh: bool = False) -> bool:
#         """Refresh user's knowledge base with latest financial data"""
#         try:
#             logger.info(f"Refreshing knowledge base for user {user_id} (force_refresh: {force_refresh})")
            
#             if force_refresh:
#                 # Remove cached data for complete refresh
#                 if user_id in self.agents:
#                     del self.agents[user_id]
#                     logger.info(f"Removed cached agent for user {user_id}")
                
#                 if user_id in self.knowledge_bases:
#                     del self.knowledge_bases[user_id]
#                     logger.info(f"Removed cached knowledge base for user {user_id}")
                
#                 if user_id in self.processed_transactions:
#                     del self.processed_transactions[user_id]
#                     logger.info(f"Cleared processed transactions tracking for user {user_id}")
                
#                 # Recreate knowledge base
#                 knowledge_base = self.create_user_knowledge_base(user_id, force_refresh=True)
#             else:
#                 # Update incrementally
#                 if user_id in self.knowledge_bases:
#                     self._update_knowledge_base_incrementally(user_id)
#                 else:
#                     knowledge_base = self.create_user_knowledge_base(user_id)
            
#             logger.info(f"Successfully refreshed knowledge base for user {user_id}")
#             return True
            
#         except Exception as e:
#             logger.error(f"Error refreshing knowledge base for user {user_id}: {e}")
#             return False

#     def get_agent_memory(self, user_id: str, session_id: Optional[str] = None) -> Dict[str, Any]:
#         """Get user's agent memory and conversation history"""
#         try:
#             agent = self.get_or_create_agent(user_id)
            
#             memory_info = {
#                 'user_id': user_id,
#                 'session_id': session_id or getattr(agent, 'session_id', None),
#                 'memories': [],
#                 'summary': None,
#                 'session_count': len(self.get_user_sessions(user_id))
#             }
            
#             # Get memories if available
#             if hasattr(agent.memory, 'get_memories'):
#                 try:
#                     memories = agent.memory.get_memories(user_id=user_id, limit=50)
#                     memory_info['memories'] = [
#                         {
#                             'content': memory.memory if hasattr(memory, 'memory') else str(memory),
#                             'created_at': memory.created_at.isoformat() if hasattr(memory, 'created_at') else None
#                         }
#                         for memory in memories
#                     ]
#                 except Exception as e:
#                     logger.warning(f"Error getting memories for user {user_id}: {e}")
            
#             # Get summary if available
#             if hasattr(agent.memory, 'get_summary'):
#                 try:
#                     summary = agent.memory.get_summary(user_id=user_id)
#                     memory_info['summary'] = summary
#                 except Exception as e:
#                     logger.warning(f"Error getting summary for user {user_id}: {e}")
            
#             return memory_info
            
#         except Exception as e:
#             logger.error(f"Error getting agent memory for user {user_id}: {e}")
#             return {
#                 'user_id': user_id,
#                 'error': str(e),
#                 'memories': [],
#                 'summary': None,
#                 'session_count': 0
#             }

#     def clear_user_data(self, user_id: str, clear_memories: bool = False) -> bool:
#         """Clear cached data for a user"""
#         try:
#             logger.info(f"Clearing cached data for user {user_id} (clear_memories: {clear_memories})")
            
#             if user_id in self.agents:
#                 if clear_memories and hasattr(self.agents[user_id], 'memory'):
#                     try:
#                         memory_db = self.agents[user_id].memory.db
#                         if hasattr(memory_db, 'clear_memories'):
#                             memory_db.clear_memories(user_id=user_id)
#                         logger.info(f"Cleared memories for user {user_id}")
#                     except Exception as e:
#                         logger.error(f"Error clearing memories for user {user_id}: {e}")
                
#                 del self.agents[user_id]
            
#             if user_id in self.knowledge_bases:
#                 del self.knowledge_bases[user_id]
            
#             if user_id in self.processed_transactions:
#                 del self.processed_transactions[user_id]
            
#             logger.info(f"Successfully cleared cached data for user {user_id}")
#             return True
            
#         except Exception as e:
#             logger.error(f"Error clearing user data for {user_id}: {e}")
#             return False

#     def health_check(self) -> Dict[str, Any]:
#         """Perform health check on the chatbot system"""
#         try:
#             health_status = {
#                 'postgres_connection': False,
#                 'vector_db_connection': False,
#                 'gemini_api': bool(GEMINI_API_KEY),
#                 'cached_agents': len(self.agents),
#                 'cached_knowledge_bases': len(self.knowledge_bases),
#                 'processed_transactions_tracking': len(self.processed_transactions),
#                 'timestamp': datetime.utcnow().isoformat()
#             }
            
#             # Test PostgreSQL connection
#             try:
#                 with self.SessionLocal() as db:
#                     db.execute(text("SELECT 1"))
#                 health_status['postgres_connection'] = True
#             except Exception as e:
#                 logger.error(f"PostgreSQL health check failed: {e}")
            
#             # Test vector DB connection
#             try:
#                 import psycopg2
#                 from urllib.parse import urlparse
#                 parsed = urlparse(self.vector_db_url)
#                 conn = psycopg2.connect(
#                     host=parsed.hostname,
#                     port=parsed.port,
#                     user=parsed.username,
#                     password=parsed.password,
#                     database=parsed.path[1:]
#                 )
#                 conn.close()
#                 health_status['vector_db_connection'] = True
#             except Exception as e:
#                 logger.error(f"Vector DB health check failed: {e}")
            
#             health_status['overall_health'] = all([
#                 health_status['postgres_connection'],
#                 health_status['vector_db_connection'],
#                 health_status['gemini_api']
#             ])
            
#             return health_status
            
#         except Exception as e:
#             logger.error(f"Health check failed: {e}")
#             return {
#                 'overall_health': False,
#                 'error': str(e),
#                 'timestamp': datetime.utcnow().isoformat()
#             }

#     def get_knowledge_base_stats(self, user_id: str) -> Dict[str, Any]:
#         """Get statistics about user's knowledge base"""
#         try:
#             stats = {
#                 'user_id': user_id,
#                 'has_knowledge_base': user_id in self.knowledge_bases,
#                 'processed_transactions_count': len(self._get_processed_transactions(user_id)),
#                 'timestamp': datetime.utcnow().isoformat()
#             }
            
#             if user_id in self.knowledge_bases:
#                 kb = self.knowledge_bases[user_id]
#                 if hasattr(kb.vector_db, 'get_document_count'):
#                     try:
#                         stats['documents_in_kb'] = kb.vector_db.get_document_count()
#                     except:
#                         stats['documents_in_kb'] = 'unknown'
#                 else:
#                     stats['documents_in_kb'] = 'unknown'
            
#             return stats
            
#         except Exception as e:
#             logger.error(f"Error getting knowledge base stats for user {user_id}: {e}")
#             return {
#                 'user_id': user_id,
#                 'error': str(e),
#                 'timestamp': datetime.utcnow().isoformat()
#             }
















import json
import re
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from sqlalchemy import create_engine, and_, desc, func
from sqlalchemy.orm import sessionmaker
import random

class FinanceChatbot:
    """
    A pattern-based chatbot that works WITHOUT any API keys.
    Perfect for demos and presentations!
    """
    
    def __init__(self, postgres_db_url: str, transaction_model, 
                 customer_model, insights_model, classification_model):
        """Initialize the pattern-based chatbot"""
        
        self.postgres_engine = create_engine(postgres_db_url, pool_pre_ping=True)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.postgres_engine)
        
        # Store models
        self.Transaction = transaction_model
        self.Customer = customer_model
        self.UserFinancialInsights = insights_model
        self.TransactionClassification = classification_model
        
        # Define response patterns
        self.patterns = self._initialize_patterns()
        
        # Session memory (simple dict-based)
        self.user_sessions = {}
        
        print("✅ Pattern-based Finance Chatbot initialized (No API keys needed!)")
    
    def _initialize_patterns(self) -> List[Dict[str, Any]]:
        """Initialize conversation patterns"""
        return [
            # Greetings
            {
                'patterns': [r'\b(hi|hello|hey|good morning|good evening)\b'],
                'handler': self._handle_greeting,
                'priority': 1
            },
            
            # Spending queries
            {
                'patterns': [
                    r'\b(spending|spent|expenses?)\b.*\b(month|today|week|year)\b',
                    r'\bshow.*spending\b',
                    r'\bhow much.*spent\b',
                    r'\bexpense.*breakdown\b'
                ],
                'handler': self._handle_spending_query,
                'priority': 2
            },
            
            # Category queries
            {
                'patterns': [
                    r'\b(category|categories)\b',
                    r'\bbiggest expense\b',
                    r'\btop spending\b',
                    r'\bwhere.*money\b',
                    r'\bspending.*category\b'
                ],
                'handler': self._handle_category_query,
                'priority': 2
            },
            
            # Income queries
            {
                'patterns': [
                    r'\b(income|salary|earned|earning)\b',
                    r'\bhow much.*earn\b',
                    r'\bincome.*source\b'
                ],
                'handler': self._handle_income_query,
                'priority': 2
            },
            
            # Savings queries
            {
                'patterns': [
                    r'\b(saving|saved|savings)\b',
                    r'\bhow much.*save\b',
                    r'\bsavings? rate\b'
                ],
                'handler': self._handle_savings_query,
                'priority': 2
            },
            
            # Transaction search
            {
                'patterns': [
                    r'\bfind.*transaction\b',
                    r'\bsearch.*for\b',
                    r'\bshow.*transaction\b.*\bto\b',
                    r'\btransaction.*to\b'
                ],
                'handler': self._handle_transaction_search,
                'priority': 2
            },
            
            # Financial health
            {
                'patterns': [
                    r'\b(financial health|health score|insights?)\b',
                    r'\bhow.*doing financially\b',
                    r'\bmy.*score\b'
                ],
                'handler': self._handle_financial_health,
                'priority': 2
            },
            
            # Monthly summary
            {
                'patterns': [
                    r'\b(monthly|month) (summary|report|overview)\b',
                    r'\bthis month\b',
                    r'\blast month\b'
                ],
                'handler': self._handle_monthly_summary,
                'priority': 2
            },
            
            # Recent transactions
            {
                'patterns': [
                    r'\brecent transactions?\b',
                    r'\blast.*transaction\b',
                    r'\bshow.*transaction\b'
                ],
                'handler': self._handle_recent_transactions,
                'priority': 2
            },
            
            # Help/What can you do
            {
                'patterns': [
                    r'\b(help|what can you|capabilities|features)\b',
                    r'\bwhat.*you do\b'
                ],
                'handler': self._handle_help,
                'priority': 1
            },
            
            # Thanks
            {
                'patterns': [r'\b(thanks?|thank you|thx)\b'],
                'handler': self._handle_thanks,
                'priority': 1
            }
        ]
    
    def _match_pattern(self, message: str) -> Optional[callable]:
        """Match message against patterns and return handler"""
        message_lower = message.lower()
        
        # Sort patterns by priority
        sorted_patterns = sorted(self.patterns, key=lambda x: x.get('priority', 999))
        
        for pattern_dict in sorted_patterns:
            for pattern in pattern_dict['patterns']:
                if re.search(pattern, message_lower):
                    return pattern_dict['handler']
        
        return None
    
    # ==================== HANDLER METHODS ====================
    
    def _handle_greeting(self, user_id: str, message: str) -> str:
        """Handle greeting messages"""
        greetings = [
            f"Hello! 👋 I'm your personal finance assistant. How can I help you today?",
            f"Hi there! 😊 Ready to explore your finances?",
            f"Hey! 🌟 What would you like to know about your finances?",
            f"Good day! 💰 I'm here to help with your financial questions!"
        ]
        
        # Add personalized greeting if we have data
        try:
            with self.SessionLocal() as db:
                customer = db.query(self.Customer).filter(
                    self.Customer.id == user_id
                ).first()
                
                if customer and hasattr(customer, 'name'):
                    return f"Hello {customer.name}! 👋 How can I help you with your finances today?"
        except:
            pass
        
        return random.choice(greetings)
    
    def _handle_spending_query(self, user_id: str, message: str) -> str:
        """Handle spending-related queries"""
        try:
            with self.SessionLocal() as db:
                # Default to last 30 days
                end_date = datetime.utcnow()
                start_date = end_date - timedelta(days=30)
                
                # Check if message mentions specific period
                if re.search(r'\btoday\b', message.lower()):
                    start_date = datetime.utcnow().replace(hour=0, minute=0, second=0)
                elif re.search(r'\bweek\b', message.lower()):
                    start_date = end_date - timedelta(days=7)
                elif re.search(r'\byear\b', message.lower()):
                    start_date = end_date - timedelta(days=365)
                
                # Get expense transactions
                expenses = db.query(
                    func.sum(self.Transaction.amount).label('total')
                ).join(
                    self.TransactionClassification,
                    self.Transaction.id == self.TransactionClassification.transaction_id
                ).filter(
                    and_(
                        self.Transaction.user_id == user_id,
                        self.Transaction.date >= start_date,
                        self.Transaction.date <= end_date,
                        self.TransactionClassification.is_income == False
                    )
                ).scalar()
                
                total_expenses = float(expenses) if expenses else 0
                
                # Get transaction count
                txn_count = db.query(func.count(self.Transaction.id)).join(
                    self.TransactionClassification,
                    self.Transaction.id == self.TransactionClassification.transaction_id
                ).filter(
                    and_(
                        self.Transaction.user_id == user_id,
                        self.Transaction.date >= start_date,
                        self.TransactionClassification.is_income == False
                    )
                ).scalar()
                
                days_diff = (end_date - start_date).days
                period_name = "today" if days_diff < 1 else f"last {days_diff} days"
                
                response = f"📊 **Spending Summary ({period_name})**\n\n"
                response += f"💸 Total Expenses: ₹{total_expenses:,.2f}\n"
                response += f"📝 Number of Transactions: {txn_count}\n"
                
                if days_diff > 1:
                    avg_daily = total_expenses / days_diff
                    response += f"📅 Average Daily Spending: ₹{avg_daily:,.2f}\n"
                
                # Add context
                if total_expenses > 50000:
                    response += f"\n💡 That's quite high! Would you like to see a category breakdown?"
                elif total_expenses < 5000:
                    response += f"\n✨ Great job keeping expenses low!"
                else:
                    response += f"\n💪 Your spending looks reasonable!"
                
                return response
                
        except Exception as e:
            return f"❌ I couldn't fetch your spending data. Error: {str(e)}"
    
    def _handle_category_query(self, user_id: str, message: str) -> str:
        """Handle category spending queries"""
        try:
            with self.SessionLocal() as db:
                end_date = datetime.utcnow()
                start_date = end_date - timedelta(days=30)
                
                # Get spending by category
                categories = db.query(
                    self.TransactionClassification.category,
                    func.sum(self.Transaction.amount).label('total'),
                    func.count(self.Transaction.id).label('count')
                ).join(
                    self.Transaction,
                    self.TransactionClassification.transaction_id == self.Transaction.id
                ).filter(
                    and_(
                        self.Transaction.user_id == user_id,
                        self.Transaction.date >= start_date,
                        self.TransactionClassification.is_income == False
                    )
                ).group_by(
                    self.TransactionClassification.category
                ).order_by(
                    desc('total')
                ).limit(5).all()
                
                if not categories:
                    return "📊 No expense categories found in the last 30 days."
                
                total = sum(float(cat.total) for cat in categories)
                
                response = "📊 **Top Spending Categories (Last 30 Days)**\n\n"
                
                emojis = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣"]
                for idx, cat in enumerate(categories):
                    percentage = (float(cat.total) / total * 100) if total > 0 else 0
                    emoji = emojis[idx] if idx < len(emojis) else "•"
                    response += f"{emoji} **{cat.category}**: ₹{float(cat.total):,.2f} ({percentage:.1f}%)\n"
                    response += f"   └─ {cat.count} transactions\n"
                
                response += f"\n💰 Total: ₹{total:,.2f}"
                
                # Add insights
                if categories[0].total / total > 0.4:
                    response += f"\n\n💡 Tip: {categories[0].category} accounts for a large portion of your spending. Consider if there's room to optimize!"
                
                return response
                
        except Exception as e:
            return f"❌ Error fetching category data: {str(e)}"
    
    def _handle_income_query(self, user_id: str, message: str) -> str:
        """Handle income queries"""
        try:
            with self.SessionLocal() as db:
                end_date = datetime.utcnow()
                start_date = end_date - timedelta(days=30)
                
                # Get income transactions
                income = db.query(
                    func.sum(self.Transaction.amount).label('total'),
                    func.count(self.Transaction.id).label('count')
                ).join(
                    self.TransactionClassification,
                    self.Transaction.id == self.TransactionClassification.transaction_id
                ).filter(
                    and_(
                        self.Transaction.user_id == user_id,
                        self.Transaction.date >= start_date,
                        self.TransactionClassification.is_income == True
                    )
                ).first()
                
                total_income = float(income.total) if income.total else 0
                txn_count = income.count if income.count else 0
                
                response = "💵 **Income Summary (Last 30 Days)**\n\n"
                response += f"✅ Total Income: ₹{total_income:,.2f}\n"
                response += f"📝 Income Transactions: {txn_count}\n"
                
                if txn_count > 0:
                    avg_income = total_income / txn_count
                    response += f"📊 Average per Transaction: ₹{avg_income:,.2f}\n"
                
                # Get income sources
                sources = db.query(
                    self.TransactionClassification.merchantName,
                    func.sum(self.Transaction.amount).label('amount')
                ).join(
                    self.Transaction,
                    self.TransactionClassification.transaction_id == self.Transaction.id
                ).filter(
                    and_(
                        self.Transaction.user_id == user_id,
                        self.Transaction.date >= start_date,
                        self.TransactionClassification.is_income == True
                    )
                ).group_by(
                    self.TransactionClassification.merchantName
                ).all()
                
                if sources:
                    response += f"\n**Income Sources:**\n"
                    for source in sources[:3]:
                        merchant = source.merchantName or "Other"
                        response += f"  • {merchant}: ₹{float(source.amount):,.2f}\n"
                
                return response
                
        except Exception as e:
            return f"❌ Error fetching income data: {str(e)}"
    
    def _handle_savings_query(self, user_id: str, message: str) -> str:
        """Handle savings queries"""
        try:
            with self.SessionLocal() as db:
                end_date = datetime.utcnow()
                start_date = end_date - timedelta(days=30)
                
                # Get income
                income = db.query(func.sum(self.Transaction.amount)).join(
                    self.TransactionClassification,
                    self.Transaction.id == self.TransactionClassification.transaction_id
                ).filter(
                    and_(
                        self.Transaction.user_id == user_id,
                        self.Transaction.date >= start_date,
                        self.TransactionClassification.is_income == True
                    )
                ).scalar()
                
                # Get expenses
                expenses = db.query(func.sum(self.Transaction.amount)).join(
                    self.TransactionClassification,
                    self.Transaction.id == self.TransactionClassification.transaction_id
                ).filter(
                    and_(
                        self.Transaction.user_id == user_id,
                        self.Transaction.date >= start_date,
                        self.TransactionClassification.is_income == False
                    )
                ).scalar()
                
                total_income = float(income) if income else 0
                total_expenses = float(expenses) if expenses else 0
                savings = total_income - total_expenses
                savings_rate = (savings / total_income * 100) if total_income > 0 else 0
                
                response = "💰 **Savings Summary (Last 30 Days)**\n\n"
                response += f"✅ Total Income: ₹{total_income:,.2f}\n"
                response += f"💸 Total Expenses: ₹{total_expenses:,.2f}\n"
                response += f"{'🎉' if savings > 0 else '⚠️'} Net Savings: ₹{savings:,.2f}\n"
                response += f"📊 Savings Rate: {savings_rate:.1f}%\n"
                
                # Add insights
                if savings_rate >= 20:
                    response += f"\n🌟 Excellent! You're saving {savings_rate:.1f}% of your income!"
                elif savings_rate >= 10:
                    response += f"\n💪 Good job! Try to push your savings rate even higher!"
                elif savings_rate > 0:
                    response += f"\n💡 Consider increasing your savings rate to at least 10%"
                else:
                    response += f"\n⚠️ Warning: Your expenses exceed your income. Let's work on reducing expenses!"
                
                return response
                
        except Exception as e:
            return f"❌ Error calculating savings: {str(e)}"
    
    def _handle_transaction_search(self, user_id: str, message: str) -> str:
        """Handle transaction search queries"""
        try:
            # Extract search keyword
            keyword_match = re.search(r'(?:to|for|about|with)\s+([a-zA-Z0-9\s]+)', message, re.IGNORECASE)
            keyword = keyword_match.group(1).strip() if keyword_match else None
            
            if not keyword:
                return "🔍 Please specify what you're looking for. Example: 'Find transactions to Amazon'"
            
            with self.SessionLocal() as db:
                transactions = db.query(self.Transaction).filter(
                    and_(
                        self.Transaction.user_id == user_id,
                        self.Transaction.narration.ilike(f"%{keyword}%")
                    )
                ).order_by(desc(self.Transaction.date)).limit(5).all()
                
                if not transactions:
                    return f"🔍 No transactions found for '{keyword}'"
                
                response = f"🔍 **Found {len(transactions)} transactions matching '{keyword}'**\n\n"
                
                for txn in transactions:
                    classification = db.query(self.TransactionClassification).filter(
                        self.TransactionClassification.transaction_id == txn.id
                    ).first()
                    
                    category = classification.category if classification else "Uncategorized"
                    date_str = txn.date.strftime("%d %b %Y")
                    
                    response += f"📅 {date_str} | ₹{float(txn.amount):,.2f}\n"
                    response += f"   {txn.narration or 'No description'}\n"
                    response += f"   Category: {category}\n\n"
                
                return response
                
        except Exception as e:
            return f"❌ Error searching transactions: {str(e)}"
    
    def _handle_financial_health(self, user_id: str, message: str) -> str:
        """Handle financial health queries"""
        try:
            with self.SessionLocal() as db:
                insights = db.query(self.UserFinancialInsights).filter(
                    self.UserFinancialInsights.user_id == user_id
                ).order_by(desc(self.UserFinancialInsights.analysisDate)).first()
                
                if not insights:
                    return "📊 No financial insights available yet. Please ensure you have transaction data."
                
                grade = insights.financialHealthGrade or "N/A"
                risk_level = insights.overallRiskLevel or "Unknown"
                savings_rate = float(insights.savingsRate) if insights.savingsRate else 0
                
                # Grade emoji
                grade_emoji = {
                    'A': '🏆', 'B': '⭐', 'C': '👍', 'D': '⚠️', 'F': '🚨'
                }.get(grade[0] if grade else 'N', '📊')
                
                response = f"{grade_emoji} **Your Financial Health Report**\n\n"
                response += f"📝 Grade: **{grade}**\n"
                response += f"⚠️ Risk Level: {risk_level}\n"
                response += f"💰 Savings Rate: {savings_rate:.1f}%\n\n"
                
                # Add strengths
                if insights.strengths:
                    response += "**💪 Strengths:**\n"
                    for strength in insights.strengths[:3]:
                        response += f"  ✓ {strength}\n"
                    response += "\n"
                
                # Add areas for improvement
                if insights.weaknesses:
                    response += "**🎯 Areas for Improvement:**\n"
                    for weakness in insights.weaknesses[:3]:
                        response += f"  → {weakness}\n"
                    response += "\n"
                
                # Add summary
                if insights.insightsSummary:
                    response += f"**📋 Summary:**\n{insights.insightsSummary}\n"
                
                return response
                
        except Exception as e:
            return f"❌ Error fetching financial health data: {str(e)}"
    
    def _handle_monthly_summary(self, user_id: str, message: str) -> str:
        """Handle monthly summary queries"""
        try:
            with self.SessionLocal() as db:
                now = datetime.utcnow()
                
                # Check if "last month" is mentioned
                if re.search(r'\blast\s+month\b', message.lower()):
                    if now.month == 1:
                        month, year = 12, now.year - 1
                    else:
                        month, year = now.month - 1, now.year
                else:
                    month, year = now.month, now.year
                
                start_date = datetime(year, month, 1)
                if month == 12:
                    end_date = datetime(year + 1, 1, 1)
                else:
                    end_date = datetime(year, month + 1, 1)
                
                # Get income and expenses
                income = db.query(func.sum(self.Transaction.amount)).join(
                    self.TransactionClassification,
                    self.Transaction.id == self.TransactionClassification.transaction_id
                ).filter(
                    and_(
                        self.Transaction.user_id == user_id,
                        self.Transaction.date >= start_date,
                        self.Transaction.date < end_date,
                        self.TransactionClassification.is_income == True
                    )
                ).scalar()
                
                expenses = db.query(func.sum(self.Transaction.amount)).join(
                    self.TransactionClassification,
                    self.Transaction.id == self.TransactionClassification.transaction_id
                ).filter(
                    and_(
                        self.Transaction.user_id == user_id,
                        self.Transaction.date >= start_date,
                        self.Transaction.date < end_date,
                        self.TransactionClassification.is_income == False
                    )
                ).scalar()
                
                total_income = float(income) if income else 0
                total_expenses = float(expenses) if expenses else 0
                savings = total_income - total_expenses
                
                month_name = start_date.strftime("%B %Y")
                
                response = f"📅 **Monthly Summary: {month_name}**\n\n"
                response += f"✅ Income: ₹{total_income:,.2f}\n"
                response += f"💸 Expenses: ₹{total_expenses:,.2f}\n"
                response += f"💰 Net Savings: ₹{savings:,.2f}\n"
                
                if total_income > 0:
                    savings_rate = (savings / total_income) * 100
                    response += f"📊 Savings Rate: {savings_rate:.1f}%\n"
                
                return response
                
        except Exception as e:
            return f"❌ Error generating monthly summary: {str(e)}"
    
    def _handle_recent_transactions(self, user_id: str, message: str) -> str:
        """Handle recent transactions queries"""
        try:
            with self.SessionLocal() as db:
                transactions = db.query(self.Transaction).filter(
                    self.Transaction.user_id == user_id
                ).order_by(desc(self.Transaction.date)).limit(5).all()
                
                if not transactions:
                    return "📭 No recent transactions found."
                
                response = "📝 **Your Recent Transactions**\n\n"
                
                for txn in transactions:
                    classification = db.query(self.TransactionClassification).filter(
                        self.TransactionClassification.transaction_id == txn.id
                    ).first()
                    
                    category = classification.category if classification else "Uncategorized"
                    is_income = classification.is_income if classification else False
                    emoji = "✅" if is_income else "💸"
                    
                    date_str = txn.date.strftime("%d %b, %I:%M %p")
                    response += f"{emoji} **₹{float(txn.amount):,.2f}** - {category}\n"
                    response += f"   {txn.narration or 'No description'}\n"
                    response += f"   {date_str}\n\n"
                
                return response
                
        except Exception as e:
            return f"❌ Error fetching recent transactions: {str(e)}"
    
    def _handle_help(self, user_id: str, message: str) -> str:
        """Handle help queries"""
        return """🤖 **I can help you with:**

💸 **Spending Analysis**
   • "Show my spending this month"
   • "How much did I spend today?"

📊 **Category Breakdown**
   • "What's my biggest expense category?"
   • "Show spending by category"

💵 **Income Tracking**
   • "How much income this month?"
   • "Show my income sources"

💰 **Savings Analysis**
   • "How much did I save?"
   • "What's my savings rate?"

🔍 **Transaction Search**
   • "Find transactions to Amazon"
   • "Search for Zomato"

📅 **Monthly Reports**
   • "Monthly summary"
   • "Last month report"

🏥 **Financial Health**
   • "Show my financial health"
   • "What's my health score?"

📝 **Recent Activity**
   • "Show recent transactions"
   • "Latest transactions"

Just ask me anything about your finances! 😊"""
    
    def _handle_thanks(self, user_id: str, message: str) -> str:
        """Handle thank you messages"""
        responses = [
            "You're welcome! 😊 Anything else I can help with?",
            "Happy to help! 🌟 Let me know if you need anything else!",
            "My pleasure! 💪 Feel free to ask more questions!",
            "Anytime! 🎉 I'm here to help with your finances!"
        ]
        return random.choice(responses)
    
    def _handle_unknown(self, user_id: str, message: str) -> str:
        """Handle unknown queries"""
        return """🤔 I'm not sure I understood that. Here are some things I can help with:

• "Show my spending this month"
• "What's my biggest expense category?"
• "How much did I save?"
• "Show recent transactions"
• "Monthly summary"
• "Financial health score"

Type 'help' to see all my capabilities! 😊"""
    
    # ==================== MAIN CHAT METHOD ====================
    
    def chat(self, user_id: str, message: str, session_id: Optional[str] = None) -> Dict[str, Any]:
        """Main chat method - process user message and return response"""
        
        try:
            if not user_id or not message:
                return {
                    "response": "Please provide a valid message.",
                    "success": False,
                    "error": "Invalid input"
                }
            
            # Initialize session if needed
            if session_id not in self.user_sessions:
                self.user_sessions[session_id or user_id] = {
                    'user_id': user_id,
                    'history': [],
                    'created_at': datetime.utcnow()
                }
            
            # Match pattern and get handler
            handler = self._match_pattern(message)
            
            # Get response
            if handler:
                response_text = handler(user_id, message)
            else:
                response_text = self._handle_unknown(user_id, message)
            
            # Store in session history
            session = self.user_sessions.get(session_id or user_id, {})
            session.setdefault('history', []).append({
                'user_message': message,
                'bot_response': response_text,
                'timestamp': datetime.utcnow().isoformat()
            })
            
            return {
                "response": response_text,
                "success": True,
                "user_id": user_id,
                "session_id": session_id or user_id,
                "timestamp": datetime.utcnow().isoformat(),
                "pattern_matched": handler.__name__ if handler else "unknown"
            }
            
        except Exception as e:
            print(f"Error in chat: {e}")
            return {
                "response": "I encountered an error. Please try again! 🔧",
                "success": False,
                "error": str(e),
                "user_id": user_id,
                "timestamp": datetime.utcnow().isoformat()
            }
    
    def get_session_history(self, session_id: str) -> List[Dict]:
        """Get conversation history for a session"""
        session = self.user_sessions.get(session_id, {})
        return session.get('history', [])
    
    def clear_session(self, session_id: str) -> bool:
        """Clear a session"""
        if session_id in self.user_sessions:
            del self.user_sessions[session_id]
            return True
        return False


