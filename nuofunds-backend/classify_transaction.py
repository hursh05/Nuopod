#!/usr/bin/env python3
"""
NuoFunds Transaction Classifier
Classifies existing transactions from webhook data and populates TransactionClassification table
"""

import asyncio
import asyncpg
import uuid
from datetime import datetime
import re
import os
from dotenv import load_dotenv

load_dotenv()
# Database connection
DATABASE_URL = os.getenv('DATABASE_URL')

# Classification rules based on narration patterns
CLASSIFICATION_RULES = {
    'income': {
        'keywords': [
            'salary', 'payout', 'earnings', 'settlement', 'bonus', 'incentive',
            'payment received', 'credit interest', 'refund', 'cashback',
            'swiggy payout', 'zomato settlement', 'ola earnings', 'uber payout',
            'freelance', 'project payment', 'invoice', 'client payment',
            'dunzo payout', 'rapido earnings', 'urban company', 'uc payment'
        ],
        'patterns': [
            r'salary.*credit',
            r'(swiggy|zomato|ola|uber|rapido|dunzo).*earnings?',
            r'(freelance|project|client).*payment',
            r'payout.*received'
        ]
    },
    'fuel': {
        'keywords': [
            'petrol', 'fuel', 'diesel', 'cng', 'gas',
            'bpcl', 'hpcl', 'iocl', 'indian oil', 'bharat petroleum',
            'hindustan petroleum', 'shell', 'reliance petrol', 'essar'
        ],
        'patterns': [
            r'(bpcl|hpcl|iocl|shell|reliance).*pump',
            r'petrol.*station',
            r'fuel.*station'
        ]
    },
    'food': {
        'keywords': [
            'restaurant', 'cafe', 'dhaba', 'hotel', 'meals', 'food',
            'swiggy', 'zomato', 'chai', 'tea', 'coffee', 'breakfast',
            'lunch', 'dinner', 'tiffin', 'biryani', 'pizza', 'burger',
            'idli', 'dosa', 'paratha', 'roti', 'thali', 'canteen'
        ],
        'patterns': [
            r'(swiggy|zomato)(?!.*payout)',
            r'(restaurant|cafe|dhaba|hotel).*payment',
            r'food.*delivery'
        ]
    },
    'travel': {
        'keywords': [
            'metro', 'bus', 'auto', 'rickshaw', 'taxi', 'cab',
            'ola', 'uber', 'rapido', 'train', 'flight', 'irctc',
            'toll', 'parking', 'fastag'
        ],
        'patterns': [
            r'(ola|uber|rapido)(?!.*payout)',
            r'(metro|bus|train).*card',
            r'(toll|parking|fastag).*payment'
        ]
    },
    'phone': {
        'keywords': [
            'mobile', 'recharge', 'prepaid', 'postpaid', 'airtel',
            'jio', 'vi', 'vodafone', 'idea', 'bsnl', 'telecom'
        ],
        'patterns': [
            r'(jio|airtel|vi|vodafone|bsnl).*recharge',
            r'mobile.*recharge',
            r'prepaid.*recharge'
        ]
    },
    'rent': {
        'keywords': [
            'rent', 'landlord', 'house rent', 'room rent', 'apartment',
            'maintenance', 'society', 'flat'
        ],
        'patterns': [
            r'(house|room|flat).*rent',
            r'landlord.*payment',
            r'rent.*payment'
        ]
    },
    'shopping': {
        'keywords': [
            'amazon', 'flipkart', 'myntra', 'ajio', 'meesho',
            'd-mart', 'dmart', 'big bazaar', 'reliance fresh', 'more',
            'supermarket', 'grocery', 'kirana', 'mall', 'store',
            'shopping', 'retail'
        ],
        'patterns': [
            r'(amazon|flipkart|myntra|meesho)',
            r'(dmart|big\s*bazaar|reliance\s*fresh)',
            r'(grocery|supermarket|mall).*payment'
        ]
    },
    'utilities': {
        'keywords': [
            'electricity', 'water', 'gas', 'lpg', 'cylinder',
            'electricity bill', 'water bill', 'bescom', 'mseb',
            'adani', 'tata power'
        ],
        'patterns': [
            r'(electricity|water|gas).*bill',
            r'(bescom|mseb|adani|tata\s*power)',
            r'lpg.*cylinder'
        ]
    },
    'entertainment': {
        'keywords': [
            'netflix', 'amazon prime', 'hotstar', 'disney', 'spotify',
            'youtube', 'movie', 'cinema', 'theatre', 'pvr', 'inox',
            'game', 'gaming'
        ],
        'patterns': [
            r'(netflix|prime|hotstar|spotify)',
            r'(pvr|inox|cinema).*ticket',
            r'movie.*ticket'
        ]
    },
    'healthcare': {
        'keywords': [
            'medicine', 'medical', 'pharmacy', 'doctor', 'hospital',
            'clinic', 'health', 'apollo', 'medplus', 'netmeds',
            'pharmeasy', 'diagnostic', 'lab', 'test'
        ],
        'patterns': [
            r'(apollo|medplus|pharmeasy|netmeds)',
            r'(hospital|clinic|doctor).*payment',
            r'medical.*store'
        ]
    },
    'education': {
        'keywords': [
            'school', 'college', 'university', 'tuition', 'course',
            'fees', 'book', 'stationery', 'education', 'udemy',
            'coursera', 'exam'
        ],
        'patterns': [
            r'(school|college|university).*fees',
            r'tuition.*payment',
            r'course.*fees'
        ]
    },
    'investment': {
        'keywords': [
            'mutual fund', 'sip', 'stock', 'zerodha', 'groww',
            'upstox', 'angel', 'investment', 'trading', 'demat'
        ],
        'patterns': [
            r'(zerodha|groww|upstox|angel)',
            r'mutual\s*fund',
            r'sip.*payment'
        ]
    },
    'insurance': {
        'keywords': [
            'insurance', 'premium', 'policy', 'lic', 'hdfc life',
            'icici pru', 'bajaj allianz', 'term insurance', 'health insurance'
        ],
        'patterns': [
            r'(lic|hdfc\s*life|icici\s*pru)',
            r'insurance.*premium',
            r'policy.*payment'
        ]
    }
}


class TransactionClassifier:
    """Classify transactions and populate TransactionClassification table"""
    
    def __init__(self):
        self.conn = None
    
    async def connect(self):
        """Connect to database"""
        self.conn = await asyncpg.connect(DATABASE_URL)
        print("✅ Connected to database")
    
    async def close(self):
        """Close connection"""
        if self.conn:
            await self.conn.close()
            print("🔌 Disconnected from database")
    
    async def classify_all_transactions(self):
        """Classify all unclassified transactions"""
        print("\n🚀 Starting transaction classification...\n")
        
        # Get all transactions that don't have classification
        unclassified = await self.conn.fetch("""
            SELECT t.*
            FROM "Transaction" t
            LEFT JOIN "TransactionClassification" tc ON t."id" = tc."transactionId"
            WHERE tc."id" IS NULL
            ORDER BY t."date" DESC
        """)
        
        if not unclassified:
            print("✅ No unclassified transactions found!")
            return
        
        print(f"📊 Found {len(unclassified)} unclassified transactions")
        print("🔍 Classifying...\n")
        
        classified_count = 0
        
        for tx in unclassified:
            classification = self._classify_transaction(tx)
            
            if classification:
                await self._save_classification(tx, classification)
                classified_count += 1
                
                if classified_count % 100 == 0:
                    print(f"  ✓ Classified {classified_count}/{len(unclassified)} transactions")
        
        print(f"\n✅ Classification complete! Classified {classified_count} transactions")
        
        # Show summary
        await self.show_classification_summary()
    
    def _classify_transaction(self, tx: dict) -> dict:
        """Classify a single transaction"""
        narration = tx['narration'].lower()
        tx_type = tx['type']
        amount = float(tx['amount'])
        
        # Determine if it's income based on type and amount
        is_income = False
        category = 'misc'
        confidence = 0.5
        
        # Credit transactions with large amounts are likely income
        if tx_type == 'CREDIT':
            # Check if it matches income patterns
            for keyword in CLASSIFICATION_RULES['income']['keywords']:
                if keyword in narration:
                    is_income = True
                    category = 'income'
                    confidence = 0.9
                    break
            
            # Check income patterns
            if not is_income:
                for pattern in CLASSIFICATION_RULES['income']['patterns']:
                    if re.search(pattern, narration, re.IGNORECASE):
                        is_income = True
                        category = 'income'
                        confidence = 0.85
                        break
            
            # If still not classified but large amount, likely income
            if not is_income and amount > 5000:
                is_income = True
                category = 'income'
                confidence = 0.7
        
        # For debit transactions or unclassified credits, check expense categories
        if not is_income:
            for cat, rules in CLASSIFICATION_RULES.items():
                if cat == 'income':
                    continue
                
                # Check keywords
                for keyword in rules['keywords']:
                    if keyword in narration:
                        category = cat
                        confidence = 0.85
                        break
                
                if category != 'misc':
                    break
                
                # Check patterns
                for pattern in rules['patterns']:
                    if re.search(pattern, narration, re.IGNORECASE):
                        category = cat
                        confidence = 0.8
                        break
                
                if category != 'misc':
                    break
        
        # Special rules for specific transaction modes
        if tx['mode'] == 'ATM' and tx_type == 'DEBIT':
            category = 'cash_withdrawal'
            confidence = 0.95
        
        return {
            'is_income': is_income,
            'category': category,
            'confidence': confidence,
            'narration_normalized': narration
        }
    
    async def _save_classification(self, tx: dict, classification: dict):
        """Save classification to database"""
        classification_id = uuid.uuid4()
        
        await self.conn.execute("""
            INSERT INTO "TransactionClassification" (
                "id", "transactionId", "userId", "isIncome",
                "category", "confidence", "narrationNormalized"
            ) VALUES (
                $1::uuid, $2::uuid, $3::uuid, $4, $5, $6, $7
            )
        """,
            classification_id,
            tx['id'],
            tx['userId'],
            classification['is_income'],
            classification['category'],
            classification['confidence'],
            classification['narration_normalized']
        )
    
    async def show_classification_summary(self):
        """Show classification summary"""
        print("\n" + "="*70)
        print("📊 CLASSIFICATION SUMMARY")
        print("="*70)
        
        # Summary by category
        summary = await self.conn.fetch("""
            SELECT 
                tc."category",
                COUNT(*) as count,
                SUM(t."amount") as total_amount,
                AVG(tc."confidence") as avg_confidence,
                CASE WHEN tc."isIncome" THEN 'Income' ELSE 'Expense' END as type
            FROM "Transaction" t
            JOIN "TransactionClassification" tc ON t."id" = tc."transactionId"
            GROUP BY tc."category", tc."isIncome"
            ORDER BY total_amount DESC
        """)
        
        print(f"\n💰 Transactions by Category:")
        print(f"{'Type':<10} | {'Category':<20} | {'Count':<8} | {'Total Amount':<15} | {'Confidence':<10}")
        print("-" * 70)
        
        for row in summary:
            print(f"{row['type']:<10} | {row['category']:<20} | "
                  f"{row['count']:<8} | ₹{float(row['total_amount']):>13,.0f} | "
                  f"{float(row['avg_confidence']):<10.2%}")
        
        # Total classified
        total_classified = await self.conn.fetchval(
            'SELECT COUNT(*) FROM "TransactionClassification"'
        )
        total_transactions = await self.conn.fetchval(
            'SELECT COUNT(*) FROM "Transaction"'
        )
        
        print(f"\n📈 Total Classified: {total_classified}/{total_transactions} "
              f"({total_classified/total_transactions*100:.1f}%)")
        
        print("\n" + "="*70)
    
    async def reclassify_specific_user(self, user_id: str):
        """Reclassify transactions for a specific user"""
        print(f"\n🔄 Reclassifying transactions for user: {user_id}")
        
        # Delete existing classifications
        deleted = await self.conn.fetchval("""
            DELETE FROM "TransactionClassification"
            WHERE "userId" = $1::uuid
            RETURNING COUNT(*)
        """, uuid.UUID(user_id))
        
        print(f"  🗑️  Deleted {deleted} existing classifications")
        
        # Reclassify
        await self.classify_all_transactions()


    async def classify_user_transactions(self, user_id: str):
        """Classify transactions for a specific user"""
        print(f"\n🚀 Classifying transactions for user: {user_id}\n")
        
        # Get unclassified transactions for this user
        unclassified = await self.conn.fetch("""
            SELECT t.*
            FROM "Transaction" t
            LEFT JOIN "TransactionClassification" tc ON t."id" = tc."transactionId"
            WHERE t."userId" = $1::uuid AND tc."id" IS NULL
            ORDER BY t."date" DESC
        """, uuid.UUID(user_id))
        
        if not unclassified:
            print(f"✅ No unclassified transactions found for user {user_id}!")
            return
        
        print(f"📊 Found {len(unclassified)} unclassified transactions for this user")
        print("🔍 Classifying...\n")
        
        classified_count = 0
        
        for tx in unclassified:
            classification = self._classify_transaction(tx)
            
            if classification:
                await self._save_classification(tx, classification)
                classified_count += 1
        
        print(f"\n✅ Classification complete! Classified {classified_count} transactions for user {user_id}")
        
        # Show user-specific summary
        await self.show_user_summary(user_id)
    
    async def show_user_summary(self, user_id: str):
        """Show classification summary for a specific user"""
        print("\n" + "="*70)
        print(f"📊 CLASSIFICATION SUMMARY - User: {user_id}")
        print("="*70)
        
        # Get user details
        user = await self.conn.fetchrow("""
            SELECT "name", "email" FROM "Customer" WHERE "id" = $1::uuid
        """, uuid.UUID(user_id))
        
        if user:
            print(f"\n👤 User: {user['name']} ({user['email']})")
        
        # Summary by category for this user
        summary = await self.conn.fetch("""
            SELECT 
                tc."category",
                COUNT(*) as count,
                SUM(t."amount") as total_amount,
                AVG(tc."confidence") as avg_confidence,
                CASE WHEN tc."isIncome" THEN 'Income' ELSE 'Expense' END as type
            FROM "Transaction" t
            JOIN "TransactionClassification" tc ON t."id" = tc."transactionId"
            WHERE t."userId" = $1::uuid
            GROUP BY tc."category", tc."isIncome"
            ORDER BY total_amount DESC
        """, uuid.UUID(user_id))
        
        print(f"\n💰 Transactions by Category:")
        print(f"{'Type':<10} | {'Category':<20} | {'Count':<8} | {'Total Amount':<15} | {'Confidence':<10}")
        print("-" * 70)
        
        for row in summary:
            print(f"{row['type']:<10} | {row['category']:<20} | "
                  f"{row['count']:<8} | ₹{float(row['total_amount']):>13,.0f} | "
                  f"{float(row['avg_confidence']):<10.2%}")
        
        # Total for this user
        total_classified = await self.conn.fetchval(
            'SELECT COUNT(*) FROM "TransactionClassification" WHERE "userId" = $1::uuid',
            uuid.UUID(user_id)
        )
        total_transactions = await self.conn.fetchval(
            'SELECT COUNT(*) FROM "Transaction" WHERE "userId" = $1::uuid',
            uuid.UUID(user_id)
        )
        
        print(f"\n📈 Total Classified: {total_classified}/{total_transactions} "
              f"({total_classified/total_transactions*100:.1f}%)")
        
        print("\n" + "="*70)


async def main():
    """Main entry point"""
    import sys
    
    classifier = TransactionClassifier()
    
    try:
        await classifier.connect()
        
        # Check if user_id is provided as command line argument
        if len(sys.argv) > 1:
            user_id = sys.argv[1]
            
            # Check if --reclassify flag is present
            if len(sys.argv) > 2 and sys.argv[2] == '--reclassify':
                print(f"🔄 Reclassifying transactions for user: {user_id}")
                await classifier.reclassify_specific_user(user_id)
            else:
                # Classify only unclassified transactions for this user
                await classifier.classify_user_transactions(user_id)
        else:
            # No user_id provided, classify all unclassified transactions
            await classifier.classify_all_transactions()
        
    finally:
        await classifier.close()
    
    print("\n✅ Done! Transactions have been classified.")
    print("\n💡 Usage:")
    print("  • Classify all users:           python classify_transactions.py")
    print("  • Classify specific user:       python classify_transactions.py <user_id>")
    print("  • Reclassify specific user:     python classify_transactions.py <user_id> --reclassify")


if __name__ == "__main__":
    asyncio.run(main())