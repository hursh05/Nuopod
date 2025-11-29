#!/usr/bin/env python3
"""
Planner Agent - Part 2
Action Card Generator and Main Runner
"""

import os
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List
import asyncpg
from dotenv import load_dotenv
import uuid

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")



class FinancialAnalyzer:
    """Analyzes user's financial data and generates insights"""
    
    def __init__(self, user_id: str, conn: asyncpg.Connection):
        self.user_id = user_id
        self.conn = conn
        self.analysis_period_days = 30
        self.insights = {}
    
    async def analyze(self) -> Dict:
        """Run complete financial analysis"""
        
        print(f"\n🔍 Analyzing financial data for user {self.user_id}...")
        
        # Gather all data
        await self._load_user_data()
        
        # Run analysis modules
        await self._analyze_income()
        await self._analyze_expenses()
        await self._analyze_savings()
        await self._analyze_cashflow()
        await self._analyze_spending_patterns()
        await self._analyze_forecast_risks()
        await self._calculate_risk_score()
        await self._determine_financial_grade()
        
        return self.insights
    
    async def _load_user_data(self):
        """Load all necessary user data"""
        
        # Daily features (last 30 days)
        self.daily_features = await self.conn.fetch("""
            SELECT * FROM "DailyFeatures"
            WHERE "userId" = $1
                AND "date" >= CURRENT_DATE - INTERVAL '30 days'
            ORDER BY "date" DESC
        """, self.user_id)
        
        # Recent transactions
        self.transactions = await self.conn.fetch("""
            SELECT t.*, tc."category", tc."isIncome"
            FROM "Transaction" t
            JOIN "TransactionClassification" tc ON tc."transactionId" = t."id"
            WHERE t."userId" = $1
                AND t."date" >= CURRENT_TIMESTAMP - INTERVAL '30 days'
            ORDER BY t."date" DESC
        """, self.user_id)
        
        # Forecasts
        self.income_forecasts = await self.conn.fetch("""
            SELECT * FROM "IncomeForecast"
            WHERE "userId" = $1
                AND "forecastDate" >= CURRENT_DATE
            ORDER BY "forecastDate"
            LIMIT 14
        """, self.user_id)
        
        self.cashflow_forecasts = await self.conn.fetch("""
            SELECT * FROM "Shortfall"
            WHERE "userId" = $1
                AND "forecastDate" >= CURRENT_DATE
            ORDER BY "forecastDate"
            LIMIT 14
        """, self.user_id)
    
    async def _analyze_income(self):
        """Analyze income patterns"""
        
        if not self.daily_features:
            return
        
        incomes = [float(row['totalIncome']) for row in self.daily_features if float(row['totalIncome']) > 0]
        
        if not incomes:
            self.insights['avgDailyIncome'] = 0
            self.insights['incomeStability'] = 'no_data'
            return
        
        avg_income = sum(incomes) / len(incomes)
        
        # Calculate coefficient of variation (CV)
        if avg_income > 0:
            std_dev = (sum((x - avg_income) ** 2 for x in incomes) / len(incomes)) ** 0.5
            cv = std_dev / avg_income
            
            # Stability classification
            if cv < 0.15:
                stability = 'stable'
                stability_score = 90
            elif cv < 0.30:
                stability = 'moderate'
                stability_score = 70
            else:
                stability = 'volatile'
                stability_score = 40
        else:
            stability = 'unknown'
            stability_score = 50
        
        # Weekly analysis
        weekly_incomes = []
        for i in range(0, len(self.daily_features), 7):
            week = self.daily_features[i:i+7]
            weekly_total = sum(float(row['totalIncome']) for row in week)
            if weekly_total > 0:
                weekly_incomes.append(weekly_total)
        
        lowest_week = min(weekly_incomes) if weekly_incomes else 0
        highest_week = max(weekly_incomes) if weekly_incomes else 0
        
        # Growth rate (comparing first 15 days vs last 15 days)
        if len(self.daily_features) >= 30:
            first_half = sum(float(row['totalIncome']) for row in self.daily_features[-30:-15])
            second_half = sum(float(row['totalIncome']) for row in self.daily_features[-15:])
            
            if first_half > 0:
                growth_rate = ((second_half - first_half) / first_half) * 100
            else:
                growth_rate = 0
        else:
            growth_rate = 0
        
        # Weekend boost
        weekend_income = sum(float(row['totalIncome']) for row in self.daily_features if row['isWeekend'])
        weekday_income = sum(float(row['totalIncome']) for row in self.daily_features if not row['isWeekend'])
        
        weekend_days = sum(1 for row in self.daily_features if row['isWeekend'])
        weekday_days = sum(1 for row in self.daily_features if not row['isWeekend'])
        
        if weekday_days > 0 and weekend_days > 0:
            avg_weekend = weekend_income / weekend_days
            avg_weekday = weekday_income / weekday_days
            weekend_boost = ((avg_weekend - avg_weekday) / avg_weekday * 100) if avg_weekday > 0 else 0
        else:
            weekend_boost = 0
        
        self.insights.update({
            'avgDailyIncome': round(avg_income, 2),
            'incomeStability': stability,
            'incomeStabilityScore': stability_score,
            'incomeGrowthRate': round(growth_rate, 2),
            'lowestIncomeWeek': round(lowest_week, 2),
            'highestIncomeWeek': round(highest_week, 2),
            'weekendIncomeBoost': round(weekend_boost, 2)
        })
    
    async def _analyze_expenses(self):
        """Analyze expense patterns"""
        
        if not self.daily_features:
            return
        
        expenses = [float(row['totalExpense']) for row in self.daily_features]
        avg_expense = sum(expenses) / len(expenses) if expenses else 0
        
        # Expense stability
        if avg_expense > 0:
            std_dev = (sum((x - avg_expense) ** 2 for x in expenses) / len(expenses)) ** 0.5
            cv = std_dev / avg_expense
            
            if cv < 0.15:
                expense_stability = 'consistent'
            elif cv < 0.30:
                expense_stability = 'variable'
            else:
                expense_stability = 'erratic'
        else:
            expense_stability = 'no_data'
        
        # Category analysis
        category_totals = {}
        for tx in self.transactions:
            if not tx['isIncome']:
                category = tx['category']
                amount = float(tx['amount'])
                category_totals[category] = category_totals.get(category, 0) + amount
        
        if category_totals:
            top_category = max(category_totals.items(), key=lambda x: x[1])
            total_expense = sum(category_totals.values())
            top_percent = (top_category[1] / total_expense * 100) if total_expense > 0 else 0
            
            # Identify unnecessary spending (high-value misc/shopping)
            unnecessary = sum(
                float(tx['amount']) for tx in self.transactions
                if not tx['isIncome'] 
                and tx['category'] in ['misc', 'shopping']
                and float(tx['amount']) > 1000
            )
        else:
            top_category = ('unknown', 0)
            top_percent = 0
            unnecessary = 0
        
        self.insights.update({
            'avgDailyExpense': round(avg_expense, 2),
            'expenseStability': expense_stability,
            'topExpenseCategory': top_category[0],
            'topExpenseCategoryAmount': round(top_category[1], 2),
            'topExpenseCategoryPercent': round(top_percent, 2),
            'unnecessarySpendingAmount': round(unnecessary, 2)
        })
    
    async def _analyze_savings(self):
        """Analyze savings patterns"""
        
        if not self.daily_features:
            return
        
        daily_savings = []
        positive_savings_days = 0
        zero_savings_days = 0
        
        for row in self.daily_features:
            net = float(row['netAmount'])
            daily_savings.append(net)
            
            if net > 0:
                positive_savings_days += 1
            elif net == 0:
                zero_savings_days += 1
        
        avg_savings = sum(daily_savings) / len(daily_savings) if daily_savings else 0
        total_savings = sum(daily_savings)
        
        # Savings rate
        total_income = sum(float(row['totalIncome']) for row in self.daily_features)
        savings_rate = (total_savings / total_income * 100) if total_income > 0 else 0
        
        # Consistency
        if positive_savings_days / len(self.daily_features) >= 0.8:
            consistency = 'always'
        elif positive_savings_days / len(self.daily_features) >= 0.6:
            consistency = 'often'
        elif positive_savings_days / len(self.daily_features) >= 0.4:
            consistency = 'sometimes'
        elif positive_savings_days / len(self.daily_features) >= 0.2:
            consistency = 'rarely'
        else:
            consistency = 'never'
        
        self.insights.update({
            'avgDailySavings': round(avg_savings, 2),
            'savingsRate': round(savings_rate, 2),
            'totalSavingsLast30Days': round(total_savings, 2),
            'savingsConsistency': consistency,
            'daysWithZeroSavings': zero_savings_days
        })
    
    async def _analyze_cashflow(self):
        """Analyze cashflow and balance patterns"""
        
        if not self.daily_features:
            return
        
        balances = [float(row['closingBalance']) for row in self.daily_features if row['closingBalance'] is not None]
        
        if not balances:
            return
        
        avg_balance = sum(balances) / len(balances)
        lowest_balance = min(balances)
        lowest_idx = balances.index(lowest_balance)
        lowest_date = self.daily_features[lowest_idx]['date']
        
        # Count low balance days (< ₹500)
        low_balance_days = sum(1 for b in balances if b < 500)
        
        # Count negative cashflow days
        negative_days = sum(1 for row in self.daily_features if float(row['netAmount']) < 0)
        
        # Cash crunch risk
        if lowest_balance < 200 or low_balance_days > 7:
            cash_crunch_risk = 'critical'
        elif lowest_balance < 500 or low_balance_days > 3:
            cash_crunch_risk = 'high'
        elif lowest_balance < 1000 or low_balance_days > 1:
            cash_crunch_risk = 'medium'
        else:
            cash_crunch_risk = 'low'
        
        self.insights.update({
            'avgDailyBalance': round(avg_balance, 2),
            'lowestBalance': round(lowest_balance, 2),
            'lowestBalanceDate': lowest_date,
            'daysWithNegativeCashflow': negative_days,
            'daysWithLowBalance': low_balance_days,
            'cashCrunchRisk': cash_crunch_risk
        })
    
    async def _analyze_spending_patterns(self):
        """Analyze spending behaviors"""
        
        if not self.transactions:
            return
        
        expense_txs = [tx for tx in self.transactions if not tx['isIncome']]
        
        if not expense_txs:
            return
        
        # Impulsive purchases (high-value, non-essential)
        impulsive = sum(
            1 for tx in expense_txs
            if float(tx['amount']) > 1000
            and tx['category'] in ['shopping', 'misc']
        )
        
        # Average transaction size
        avg_tx_size = sum(float(tx['amount']) for tx in expense_txs) / len(expense_txs)
        
        # High-value transaction count
        high_value = sum(1 for tx in expense_txs if float(tx['amount']) > 1000)
        
        # Spending pattern type
        if impulsive > 5 or high_value > 10:
            pattern_type = 'impulsive'
        elif impulsive > 2 or high_value > 5:
            pattern_type = 'moderate'
        else:
            pattern_type = 'controlled'
        
        # Peak spending day/time
        day_counts = {}
        for tx in expense_txs:
            day = tx['date'].strftime('%A')
            day_counts[day] = day_counts.get(day, 0) + 1
        
        peak_day = max(day_counts.items(), key=lambda x: x[1])[0] if day_counts else 'Unknown'
        
        # Peak spending time
        hour_counts = {'morning': 0, 'afternoon': 0, 'evening': 0}
        for tx in expense_txs:
            hour = tx['date'].hour
            if 6 <= hour < 12:
                hour_counts['morning'] += 1
            elif 12 <= hour < 18:
                hour_counts['afternoon'] += 1
            else:
                hour_counts['evening'] += 1
        
        peak_time = max(hour_counts.items(), key=lambda x: x[1])[0]
        
        self.insights.update({
            'impulsivePurchases': impulsive,
            'spendingPatternType': pattern_type,
            'averageTransactionSize': round(avg_tx_size, 2),
            'highValueTransactions': high_value,
            'spendingPeakDay': peak_day,
            'spendingPeakTime': peak_time
        })
    
    async def _analyze_forecast_risks(self):
        """Analyze upcoming risks from forecasts"""
        
        if not self.cashflow_forecasts:
            return
        
        shortfall_days = 0
        total_shortfall = 0
        next_low_balance_date = None
        
        for fc in self.cashflow_forecasts:
            shortfall = float(fc['predictedShortfall'])
            if shortfall < 0:
                shortfall_days += 1
                total_shortfall += abs(shortfall)
                
                if next_low_balance_date is None:
                    next_low_balance_date = fc['forecastDate']
        
        self.insights.update({
            'predictedShortfallDays': shortfall_days,
            'predictedShortfallAmount': round(total_shortfall, 2),
            'nextLowBalanceDate': next_low_balance_date
        })
    
    async def _calculate_risk_score(self):
        """Calculate overall risk score (0-100)"""
        
        risk_score = 0
        risk_factors = []
        strengths = []
        weaknesses = []
        
        # Income stability (20 points)
        income_stability_score = self.insights.get('incomeStabilityScore', 50)
        risk_score += (income_stability_score / 100) * 20
        
        if income_stability_score < 50:
            risk_factors.append('Highly volatile income')
            weaknesses.append('Inconsistent earnings pattern')
        else:
            strengths.append('Stable income source')
        
        # Savings rate (25 points)
        savings_rate = self.insights.get('savingsRate', 0)
        if savings_rate > 20:
            risk_score += 25
            strengths.append(f'Good savings rate ({savings_rate:.1f}%)')
        elif savings_rate > 10:
            risk_score += 15
        elif savings_rate > 0:
            risk_score += 5
            weaknesses.append('Low savings rate')
        else:
            risk_factors.append('No savings')
            weaknesses.append('Unable to save money')
        
        # Balance health (20 points)
        avg_balance = self.insights.get('avgDailyBalance', 0)
        if avg_balance > 5000:
            risk_score += 20
            strengths.append('Healthy balance maintained')
        elif avg_balance > 2000:
            risk_score += 10
        elif avg_balance > 500:
            risk_score += 5
        else:
            risk_factors.append('Very low balance')
            weaknesses.append('Insufficient emergency buffer')
        
        # Cashflow consistency (15 points)
        negative_days = self.insights.get('daysWithNegativeCashflow', 0)
        if negative_days == 0:
            risk_score += 15
        elif negative_days < 3:
            risk_score += 10
        elif negative_days < 7:
            risk_score += 5
            weaknesses.append('Frequent negative cashflow days')
        else:
            risk_factors.append('Frequent negative cashflow')
            weaknesses.append('Poor cashflow management')
        
        # Spending control (10 points)
        if self.insights.get('spendingPatternType') == 'controlled':
            risk_score += 10
            strengths.append('Controlled spending habits')
        elif self.insights.get('spendingPatternType') == 'moderate':
            risk_score += 5
        else:
            risk_factors.append('Impulsive spending')
            weaknesses.append('Need better expense control')
        
        # Forecast risks (10 points)
        shortfall_days = self.insights.get('predictedShortfallDays', 0)
        if shortfall_days == 0:
            risk_score += 10
        elif shortfall_days < 3:
            risk_score += 5
        else:
            risk_factors.append(f'{shortfall_days} shortfall days ahead')
            weaknesses.append('High shortfall risk in coming days')
        
        # Overall risk level
        if risk_score >= 80:
            risk_level = 'low'
        elif risk_score >= 60:
            risk_level = 'medium'
        elif risk_score >= 40:
            risk_level = 'high'
        else:
            risk_level = 'critical'
        
        # Recommendations
        avg_income = self.insights.get('avgDailyIncome', 1000)
        recommended_daily_savings = max(avg_income * 0.1, 50)  # 10% of income or ₹50
        recommended_emergency_fund = avg_income * 30  # 1 month's income
        
        current_savings = self.insights.get('totalSavingsLast30Days', 0)
        if current_savings > 0:
            months_to_fund = recommended_emergency_fund / (current_savings / 30)
        else:
            months_to_fund = 999
        
        self.insights.update({
            'overallRiskLevel': risk_level,
            'riskScore': round(risk_score, 2),
            'riskFactors': risk_factors,
            'strengths': strengths,
            'weaknesses': weaknesses,
            'recommendedDailySavings': round(recommended_daily_savings, 2),
            'recommendedEmergencyFund': round(recommended_emergency_fund, 2),
            'monthsToEmergencyFund': round(months_to_fund, 2)
        })
    
    async def _determine_financial_grade(self):
        """Assign financial health grade"""
        
        risk_score = self.insights.get('riskScore', 0)
        
        if risk_score >= 90:
            grade = 'A+'
        elif risk_score >= 85:
            grade = 'A'
        elif risk_score >= 75:
            grade = 'B+'
        elif risk_score >= 65:
            grade = 'B'
        elif risk_score >= 50:
            grade = 'C'
        else:
            grade = 'D'
        
        # Generate summary
        summary = self._generate_summary()
        
        self.insights.update({
            'financialHealthGrade': grade,
            'insightsSummary': summary
        })
    
    def _generate_summary(self) -> str:
        """Generate human-readable summary"""
        
        avg_income = self.insights.get('avgDailyIncome', 0)
        savings_rate = self.insights.get('savingsRate', 0)
        risk_level = self.insights.get('overallRiskLevel', 'unknown')
        
        summary = f"Daily income ₹{avg_income:.0f}, saving {savings_rate:.1f}% of earnings. "
        summary += f"Financial risk: {risk_level}. "
        
        if self.insights.get('predictedShortfallDays', 0) > 0:
            summary += f"⚠️ {self.insights['predictedShortfallDays']} shortfall days predicted. "
        
        return summary


class ActionCardGenerator:
    """Generates personalized action cards based on insights"""
    
    def __init__(self, user_id: str, insights: Dict, conn: asyncpg.Connection):
        self.user_id = user_id
        self.insights = insights
        self.conn = conn
        self.action_cards = []
    
    async def generate_all_cards(self) -> List[Dict]:
        """Generate all relevant action cards"""
        
        print(f"\n💡 Generating action cards...")
        
        # Generate different types of cards
        await self._generate_shortfall_alerts()
        await self._generate_savings_recommendations()
        await self._generate_expense_reduction_cards()
        await self._generate_milestone_cards()
        await self._generate_risk_alerts()
        
        return self.action_cards
    
    async def _generate_shortfall_alerts(self):
        """Generate alerts for predicted shortfalls"""
        
        shortfall_days = self.insights.get('predictedShortfallDays', 0)
        
        if shortfall_days == 0:
            return
        
        shortfall_amount = self.insights.get('predictedShortfallAmount', 0)
        next_date = self.insights.get('nextLowBalanceDate')
        
        if next_date:
            days_until = (next_date - datetime.now().date()).days
            
            card = {
                'cardType': 'emergency_alert',
                'priority': 'urgent' if days_until <= 3 else 'high',
                'category': 'risk',
                'title': '⚠️ Low Balance Alert',
                'message': f'You might face a cash shortage in {days_until} days. Total predicted shortfall: ₹{shortfall_amount:.0f}',
                'messageHindi': f'आपको {days_until} दिनों में पैसों की कमी हो सकती है। कुल कमी: ₹{shortfall_amount:.0f}',
                'icon': '⚠️',
                'color': 'red',
                'actionType': 'prepare_emergency',
                'actionAmount': shortfall_amount,
                'actionDescription': f'Consider: 1) Reducing expenses, 2) Finding extra work, 3) Using emergency fund',
                'expectedSavings': shortfall_amount,
                'expectedImpactDays': days_until,
                'impactDescription': f'Preparing now can prevent zero balance on {next_date}',
                'validFrom': datetime.now(),
                'validUntil': datetime.now() + timedelta(days=days_until),
                'isUrgent': days_until <= 3,
                'daysUntilImpact': days_until
            }
            
            self.action_cards.append(card)
    
    async def _generate_savings_recommendations(self):
        """Generate savings recommendations"""
        
        avg_income = self.insights.get('avgDailyIncome', 0)
        current_savings_rate = self.insights.get('savingsRate', 0)
        
        if current_savings_rate < 10 and avg_income > 0:
            # Recommend starting to save
            recommended_amount = self.insights.get('recommendedDailySavings', 100)
            
            card = {
                'cardType': 'save_now',
                'priority': 'high' if current_savings_rate == 0 else 'medium',
                'category': 'savings',
                'title': '💰 Start Saving Today',
                'message': f'Try saving just ₹{recommended_amount:.0f}/day. In a month, you\'ll have ₹{recommended_amount * 30:.0f}!',
                'messageHindi': f'रोज़ सिर्फ ₹{recommended_amount:.0f} बचाएं। महीने में ₹{recommended_amount * 30:.0f} जमा होंगे!',
                'icon': '💰',
                'color': 'green',
                'actionType': 'save_amount',
                'actionAmount': recommended_amount,
                'actionDescription': 'Set aside this amount daily, even if it means skipping one chai',
                'expectedSavings': recommended_amount * 30,
                'expectedImpactDays': 30,
                'impactDescription': f'Building emergency fund of ₹{recommended_amount * 30:.0f}/month',
                'validFrom': datetime.now(),
                'validUntil': datetime.now() + timedelta(days=7)
            }
            
            self.action_cards.append(card)
    
    async def _generate_expense_reduction_cards(self):
        """Generate expense reduction recommendations"""
        
        top_category = self.insights.get('topExpenseCategory')
        top_amount = self.insights.get('topExpenseCategoryAmount', 0)
        unnecessary = self.insights.get('unnecessarySpendingAmount', 0)
        
        # High spending category alert
        if top_category and top_amount > 0:
            avg_income = self.insights.get('avgDailyIncome', 1)
            percent_of_income = (top_amount / (avg_income * 30)) * 100 if avg_income > 0 else 0
            
            if percent_of_income > 30:  # Spending > 30% on one category
                reduction_target = top_amount * 0.2  # Reduce by 20%
                
                card = {
                    'cardType': 'reduce_expense',
                    'priority': 'medium',
                    'category': 'expense',
                    'title': f'🎯 Reduce {top_category.title()} Spending',
                    'message': f'You spent ₹{top_amount:.0f} on {top_category} last month. Try reducing by ₹{reduction_target:.0f}',
                    'messageHindi': f'पिछले महीने {top_category} पर ₹{top_amount:.0f} खर्च हुए। ₹{reduction_target:.0f} कम करने की कोशिश करें',
                    'icon': '🎯',
                    'color': 'yellow',
                    'actionType': 'reduce_category_spend',
                    'actionAmount': reduction_target,
                    'actionCategory': top_category,
                    'actionDescription': f'Small cuts add up. Look for cheaper alternatives for {top_category}',
                    'expectedSavings': reduction_target,
                    'expectedImpactDays': 30,
                    'impactDescription': f'Saving ₹{reduction_target:.0f} can improve your emergency fund',
                    'validFrom': datetime.now(),
                    'validUntil': datetime.now() + timedelta(days=30)
                }
                
                self.action_cards.append(card)
        
        # Unnecessary spending alert
        if unnecessary > 1000:
            card = {
                'cardType': 'delay_purchase',
                'priority': 'medium',
                'category': 'expense',
                'title': '🛑 Avoid Impulse Buys',
                'message': f'You made ₹{unnecessary:.0f} in large impulse purchases. Think before buying!',
                'messageHindi': f'आपने ₹{unnecessary:.0f} की बड़ी खरीदारी की। खरीदने से पहले सोचें!',
                'icon': '🛑',
                'color': 'orange',
                'actionType': 'skip_purchase',
                'actionAmount': unnecessary,
                'actionDescription': 'Wait 24 hours before making purchases over ₹1000',
                'expectedSavings': unnecessary * 0.5,  # Could save 50% by delaying
                'expectedImpactDays': 30,
                'impactDescription': 'Avoiding impulse buys saves significant money',
                'validFrom': datetime.now(),
                'validUntil': datetime.now() + timedelta(days=30)
            }
            
            self.action_cards.append(card)
    
    async def _generate_milestone_cards(self):
        """Generate positive milestone cards"""
        
        savings_rate = self.insights.get('savingsRate', 0)
        consistency = self.insights.get('savingsConsistency')
        
        # Positive reinforcement
        if savings_rate > 15:
            card = {
                'cardType': 'milestone_achieved',
                'priority': 'low',
                'category': 'goal',
                'title': '🎉 Great Job Saving!',
                'message': f'You\'re saving {savings_rate:.1f}% of your income. Keep it up!',
                'messageHindi': f'आप अपनी कमाई का {savings_rate:.1f}% बचा रहे हैं। बढ़िया!',
                'icon': '🎉',
                'color': 'green',
                'actionType': 'continue_habit',
                'actionDescription': 'Your savings habit is strong. Maintain this momentum!',
                'expectedImpactDays': 30,
                'impactDescription': 'Consistent savings build long-term security',
                'validFrom': datetime.now(),
                'validUntil': datetime.now() + timedelta(days=7)
            }
            
            self.action_cards.append(card)
        
        elif consistency == 'often':
            card = {
                'cardType': 'milestone_achieved',
                'priority': 'low',
                'category': 'goal',
                'title': '👍 Good Progress',
                'message': 'You\'re saving regularly! Try to make it daily.',
                'messageHindi': 'आप नियमित रूप से बचत कर रहे हैं! रोज़ बचाने की कोशिश करें।',
                'icon': '👍',
                'color': 'blue',
                'actionType': 'improve_consistency',
                'actionDescription': 'Aim to save something every day, even if it\'s small',
                'validFrom': datetime.now(),
                'validUntil': datetime.now() + timedelta(days=7)
            }
            
            self.action_cards.append(card)
    
    async def _generate_risk_alerts(self):
        """Generate risk-based alerts"""
        
        risk_level = self.insights.get('overallRiskLevel')
        low_balance_days = self.insights.get('daysWithLowBalance', 0)
        
        if risk_level == 'critical':
            card = {
                'cardType': 'emergency_alert',
                'priority': 'urgent',
                'category': 'risk',
                'title': '🚨 Critical: Take Action Now',
                'message': 'Your financial health needs immediate attention. Review your expenses urgently.',
                'messageHindi': '🚨 गंभीर: तुरंत कार्रवाई करें। अपने खर्चों की तुरंत समीक्षा करें।',
                'icon': '🚨',
                'color': 'red',
                'actionType': 'emergency_review',
                'actionDescription': '1) Cut all non-essential spending, 2) Find additional income, 3) Consider emergency support',
                'validFrom': datetime.now(),
                'validUntil': datetime.now() + timedelta(days=3),
                'isUrgent': True
            }
            
            self.action_cards.append(card)
        
        elif low_balance_days > 5:
            card = {
                'cardType': 'emergency_alert',
                'priority': 'high',
                'category': 'risk',
                'title': '⚠️ Low Balance Warning',
                'message': f'Your balance was below ₹500 for {low_balance_days} days. Build an emergency buffer.',
                'messageHindi': f'आपका बैलेंस {low_balance_days} दिनों तक ₹500 से कम था। आपातकालीन फंड बनाएं।',
                'icon': '⚠️',
                'color': 'red',
                'actionType': 'build_buffer',
                'actionDescription': 'Try to maintain at least ₹1000 buffer at all times',
                'validFrom': datetime.now(),
                'validUntil': datetime.now() + timedelta(days=7)
            }
            
            self.action_cards.append(card)


# class PlannerAgent:
#     """Main Planner Agent orchestrator"""
    
#     def __init__(self):
#         self.conn = None
    
#     async def connect(self):
#         """Connect to database"""
#         self.conn = await asyncpg.connect(DATABASE_URL)
#         print("✅ Connected to database")
    
#     async def close(self):
#         """Close connection"""
#         if self.conn:
#             await self.conn.close()
#             print("🔌 Disconnected from database")
    
#     async def run_for_user(self, user_id: str):
#         """Run complete planning process for one user"""
        
#         print(f"\n{'='*60}")
#         print(f"🤖 PLANNER AGENT - User: {user_id}")
#         print(f"{'='*60}")
        
#         try:
#             # Step 1: Analyze financial data
#             analyzer = FinancialAnalyzer(user_id, self.conn)
#             insights = await analyzer.analyze()
            
#             # Step 2: Save insights to database
#             insight_id = await self._save_insights(user_id, insights)
            
#             # Step 3: Generate action cards
#             card_generator = ActionCardGenerator(user_id, insights, self.conn)
#             action_cards = await card_generator.generate_all_cards()
            
#             # Step 4: Save action cards
#             await self._save_action_cards(user_id, insight_id, action_cards)
            
#             # Step 5: Print summary
#             self._print_summary(insights, action_cards)
            
#             return {
#                 'status': 'success',
#                 'insights': insights,
#                 'action_cards_count': len(action_cards)
#             }
            
#         except Exception as e:
#             print(f"❌ Error: {e}")
#             import traceback
#             traceback.print_exc()
#             return {'status': 'error', 'message': str(e)}
    
#     async def _save_insights(self, user_id: str, insights: Dict) -> str:
#         """Save insights to database"""
        
#         print("\n💾 Saving insights to database...")
        
#         insight_id = await self.conn.fetchval("""
#             INSERT INTO "UserFinancialInsights" (
#                 "userId", "analysisDate", "analysisPeriodDays",
#                 "avgDailyIncome", "incomeStability", "incomeStabilityScore",
#                 "incomeGrowthRate", "lowestIncomeWeek", "highestIncomeWeek",
#                 "weekendIncomeBoost", "avgDailyExpense", "expenseStability",
#                 "topExpenseCategory", "topExpenseCategoryAmount", "topExpenseCategoryPercent",
#                 "unnecessarySpendingAmount", "avgDailySavings", "savingsRate",
#                 "totalSavingsLast30Days", "savingsConsistency", "daysWithZeroSavings",
#                 "avgDailyBalance", "lowestBalance", "lowestBalanceDate",
#                 "daysWithNegativeCashflow", "daysWithLowBalance", "cashCrunchRisk",
#                 "impulsivePurchases", "spendingPatternType", "averageTransactionSize",
#                 "highValueTransactions", "overallRiskLevel", "riskScore",
#                 "riskFactors", "strengths", "weaknesses",
#                 "recommendedDailySavings", "recommendedEmergencyFund", "monthsToEmergencyFund",
#                 "spendingPeakDay", "spendingPeakTime",
#                 "predictedShortfallDays", "predictedShortfallAmount", "nextLowBalanceDate",
#                 "financialHealthGrade", "insightsSummary"
#             ) VALUES (
#                 $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15,
#                 $16, $17, $18, $19, $20, $21, $22, $23, $24, $25, $26, $27, $28,
#                 $29, $30, $31, $32, $33, $34, $35, $36, $37, $38, $39, $40, $41,
#                 $42, $43, $44, $45, $46
#             )
#             RETURNING "id"
#         """,
#             user_id, datetime.now(), 30,
#             insights.get('avgDailyIncome'), insights.get('incomeStability'), 
#             insights.get('incomeStabilityScore'), insights.get('incomeGrowthRate'),
#             insights.get('lowestIncomeWeek'), insights.get('highestIncomeWeek'),
#             insights.get('weekendIncomeBoost'), insights.get('avgDailyExpense'),
#             insights.get('expenseStability'), insights.get('topExpenseCategory'),
#             insights.get('topExpenseCategoryAmount'), insights.get('topExpenseCategoryPercent'),
#             insights.get('unnecessarySpendingAmount'), insights.get('avgDailySavings'),
#             insights.get('savingsRate'), insights.get('totalSavingsLast30Days'),
#             insights.get('savingsConsistency'), insights.get('daysWithZeroSavings'),
#             insights.get('avgDailyBalance'), insights.get('lowestBalance'),
#             insights.get('lowestBalanceDate'), insights.get('daysWithNegativeCashflow'),
#             insights.get('daysWithLowBalance'), insights.get('cashCrunchRisk'),
#             insights.get('impulsivePurchases'), insights.get('spendingPatternType'),
#             insights.get('averageTransactionSize'), insights.get('highValueTransactions'),
#             insights.get('overallRiskLevel'), insights.get('riskScore'),
#             insights.get('riskFactors', []), insights.get('strengths', []),
#             insights.get('weaknesses', []), insights.get('recommendedDailySavings'),
#             insights.get('recommendedEmergencyFund'), insights.get('monthsToEmergencyFund'),
#             insights.get('spendingPeakDay'), insights.get('spendingPeakTime'),
#             insights.get('predictedShortfallDays'), insights.get('predictedShortfallAmount'),
#             insights.get('nextLowBalanceDate'), insights.get('financialHealthGrade'),
#             insights.get('insightsSummary')
#         )
        
#         print(f"✅ Saved insights (ID: {insight_id})")
#         return insight_id
    
#     async def _save_action_cards(self, user_id: str, insight_id: str, action_cards: List[Dict]):
#         """Save action cards to database"""
        
#         print(f"\n💾 Saving {len(action_cards)} action cards...")
        
#         for card in action_cards:
#             await self.conn.execute("""
#                 INSERT INTO "ActionCard" (
#                     "userId", "insightId", "cardType", "priority", "category",
#                     "title", "message", "messageHindi", "icon", "color",
#                     "actionType", "actionAmount", "actionCategory", "actionDescription",
#                     "expectedSavings", "expectedImpactDays", "impactDescription",
#                     "validFrom", "validUntil", "isUrgent", "daysUntilImpact"
#                 ) VALUES (
#                     $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14,
#                     $15, $16, $17, $18, $19, $20, $21
#                 )
#             """,
#                 user_id, insight_id, card['cardType'], card['priority'], card.get('category'),
#                 card['title'], card['message'], card.get('messageHindi'), 
#                 card.get('icon'), card.get('color'),
#                 card.get('actionType'), card.get('actionAmount'), card.get('actionCategory'),
#                 card.get('actionDescription'), card.get('expectedSavings'),
#                 card.get('expectedImpactDays'), card.get('impactDescription'),
#                 card.get('validFrom'), card.get('validUntil'),
#                 card.get('isUrgent', False), card.get('daysUntilImpact')
#             )
        
#         print(f"✅ Saved {len(action_cards)} action cards")
    
#     def _print_summary(self, insights: Dict, action_cards: List[Dict]):
#         """Print summary of analysis"""
        
#         print(f"\n{'='*60}")
#         print("📊 FINANCIAL ANALYSIS SUMMARY")
#         print(f"{'='*60}")
        
#         print(f"\n💰 Income:")
#         print(f"  Avg Daily: ₹{insights.get('avgDailyIncome', 0):.0f}")
#         print(f"  Stability: {insights.get('incomeStability')} ({insights.get('incomeStabilityScore', 0):.0f}/100)")
#         print(f"  Growth: {insights.get('incomeGrowthRate', 0):+.1f}%")
        
#         print(f"\n💸 Expenses:")
#         print(f"  Avg Daily: ₹{insights.get('avgDailyExpense', 0):.0f}")
#         print(f"  Top Category: {insights.get('topExpenseCategory')} (₹{insights.get('topExpenseCategoryAmount', 0):.0f})")
#         print(f"  Unnecessary: ₹{insights.get('unnecessarySpendingAmount', 0):.0f}")
        
#         print(f"\n💵 Savings:")
#         print(f"  Avg Daily: ₹{insights.get('avgDailySavings', 0):.0f}")
#         print(f"  Rate: {insights.get('savingsRate', 0):.1f}%")
#         print(f"  Consistency: {insights.get('savingsConsistency')}")
        
#         print(f"\n⚠️ Risk Assessment:")
#         print(f"  Overall: {insights.get('overallRiskLevel')} (Score: {insights.get('riskScore', 0):.0f}/100)")
#         print(f"  Grade: {insights.get('financialHealthGrade')}")
#         print(f"  Cash Crunch: {insights.get('cashCrunchRisk')}")
        
#         if insights.get('riskFactors'):
#             print(f"\n  Risk Factors:")
#             for factor in insights['riskFactors']:
#                 print(f"    ❌ {factor}")
        
#         if insights.get('strengths'):
#             print(f"\n  Strengths:")
#             for strength in insights['strengths']:
#                 print(f"    ✅ {strength}")
        
#         print(f"\n📋 Action Cards Generated: {len(action_cards)}")
#         for card in action_cards:
#             priority_emoji = {
#                 'urgent': '🔴',
#                 'high': '🟠',
#                 'medium': '🟡',
#                 'low': '🟢'
#             }.get(card['priority'], '⚪')
            
#             print(f"  {priority_emoji} [{card['priority'].upper()}] {card['title']}")
        
#         print(f"\n{'='*60}")
    
#     async def run_for_all_users(self):
#         """Run planner for all users"""
        
#         # Get all user IDs
#         user_ids = await self.conn.fetch('SELECT "id" FROM "Customer"')
        
#         print(f"\n📊 Running Planner Agent for {len(user_ids)} users...\n")
        
#         success_count = 0
#         for row in user_ids:
#             result = await self.run_for_user(row['id'])
#             if result['status'] == 'success':
#                 success_count += 1
        
#         print(f"\n{'='*60}")
#         print(f"✅ Completed: {success_count}/{len(user_ids)} users")
#         print(f"{'='*60}")


class PlannerAgent:
    """Main Planner Agent orchestrator"""
    
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
    
    async def run_for_user(self, user_id: str):
        """Run complete planning process for one user"""
        
        print(f"\n{'='*60}")
        print(f"🤖 PLANNER AGENT - User: {user_id}")
        print(f"{'='*60}")
        
        try:
            # Step 1: Analyze financial data
            analyzer = FinancialAnalyzer(user_id, self.conn)
            insights = await analyzer.analyze()
            
            # Step 2: Save insights to database
            insight_id = await self._save_insights(user_id, insights)
            
            # Step 3: Generate action cards
            card_generator = ActionCardGenerator(user_id, insights, self.conn)
            action_cards = await card_generator.generate_all_cards()
            
            # Step 4: Save action cards
            await self._save_action_cards(user_id, insight_id, action_cards)
            
            # Step 5: Print summary
            self._print_summary(insights, action_cards)
            
            return {
                'status': 'success',
                'insights': insights,
                'action_cards_count': len(action_cards)
            }
            
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
            return {'status': 'error', 'message': str(e)}
    
    async def _save_insights(self, user_id: str, insights: Dict) -> str:
        """Save insights to database with UUID generation"""
        
        print("\n💾 Saving insights to database...")
        
        # ✅ Generate UUID for the insight record
        insight_id = str(uuid.uuid4())
        
        await self.conn.execute("""
            INSERT INTO "UserFinancialInsights" (
                "id",
                "userId", "analysisDate", "analysisPeriodDays",
                "avgDailyIncome", "incomeStability", "incomeStabilityScore",
                "incomeGrowthRate", "lowestIncomeWeek", "highestIncomeWeek",
                "weekendIncomeBoost", "avgDailyExpense", "expenseStability",
                "topExpenseCategory", "topExpenseCategoryAmount", "topExpenseCategoryPercent",
                "unnecessarySpendingAmount", "avgDailySavings", "savingsRate",
                "totalSavingsLast30Days", "savingsConsistency", "daysWithZeroSavings",
                "avgDailyBalance", "lowestBalance", "lowestBalanceDate",
                "daysWithNegativeCashflow", "daysWithLowBalance", "cashCrunchRisk",
                "impulsivePurchases", "spendingPatternType", "averageTransactionSize",
                "highValueTransactions", "overallRiskLevel", "riskScore",
                "riskFactors", "strengths", "weaknesses",
                "recommendedDailySavings", "recommendedEmergencyFund", "monthsToEmergencyFund",
                "spendingPeakDay", "spendingPeakTime",
                "predictedShortfallDays", "predictedShortfallAmount", "nextLowBalanceDate",
                "financialHealthGrade", "insightsSummary"
            ) VALUES (
                $1,
                $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16,
                $17, $18, $19, $20, $21, $22, $23, $24, $25, $26, $27, $28, $29,
                $30, $31, $32, $33, $34, $35, $36, $37, $38, $39, $40, $41, $42,
                $43, $44, $45, $46, $47
            )
        """,
            insight_id,  # $1 - ✅ Generated UUID
            user_id, datetime.now(), 30,  # $2, $3, $4
            insights.get('avgDailyIncome'), insights.get('incomeStability'),  # $5, $6
            insights.get('incomeStabilityScore'), insights.get('incomeGrowthRate'),  # $7, $8
            insights.get('lowestIncomeWeek'), insights.get('highestIncomeWeek'),  # $9, $10
            insights.get('weekendIncomeBoost'), insights.get('avgDailyExpense'),  # $11, $12
            insights.get('expenseStability'), insights.get('topExpenseCategory'),  # $13, $14
            insights.get('topExpenseCategoryAmount'), insights.get('topExpenseCategoryPercent'),  # $15, $16
            insights.get('unnecessarySpendingAmount'), insights.get('avgDailySavings'),  # $17, $18
            insights.get('savingsRate'), insights.get('totalSavingsLast30Days'),  # $19, $20
            insights.get('savingsConsistency'), insights.get('daysWithZeroSavings'),  # $21, $22
            insights.get('avgDailyBalance'), insights.get('lowestBalance'),  # $23, $24
            insights.get('lowestBalanceDate'), insights.get('daysWithNegativeCashflow'),  # $25, $26
            insights.get('daysWithLowBalance'), insights.get('cashCrunchRisk'),  # $27, $28
            insights.get('impulsivePurchases'), insights.get('spendingPatternType'),  # $29, $30
            insights.get('averageTransactionSize'), insights.get('highValueTransactions'),  # $31, $32
            insights.get('overallRiskLevel'), insights.get('riskScore'),  # $33, $34
            insights.get('riskFactors', []), insights.get('strengths', []),  # $35, $36
            insights.get('weaknesses', []), insights.get('recommendedDailySavings'),  # $37, $38
            insights.get('recommendedEmergencyFund'), insights.get('monthsToEmergencyFund'),  # $39, $40
            insights.get('spendingPeakDay'), insights.get('spendingPeakTime'),  # $41, $42
            insights.get('predictedShortfallDays'), insights.get('predictedShortfallAmount'),  # $43, $44
            insights.get('nextLowBalanceDate'), insights.get('financialHealthGrade'),  # $45, $46
            insights.get('insightsSummary')  # $47
        )
        
        print(f"✅ Saved insights (ID: {insight_id})")
        return insight_id
    
    async def _save_action_cards(self, user_id: str, insight_id: str, action_cards: List[Dict]):
        """Save action cards to database with UUID generation"""
        
        print(f"\n💾 Saving {len(action_cards)} action cards...")
        
        for card in action_cards:
            # ✅ Generate UUID for each action card
            card_id = str(uuid.uuid4())
            
            await self.conn.execute("""
                INSERT INTO "ActionCard" (
                    "id",
                    "userId", "insightId", "cardType", "priority", "category",
                    "title", "message", "messageHindi", "icon", "color",
                    "actionType", "actionAmount", "actionCategory", "actionDescription",
                    "expectedSavings", "expectedImpactDays", "impactDescription",
                    "validFrom", "validUntil", "isUrgent", "daysUntilImpact"
                ) VALUES (
                    $1,
                    $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15,
                    $16, $17, $18, $19, $20, $21, $22
                )
            """,
                card_id,  # $1 - ✅ Generated UUID
                user_id, insight_id, card['cardType'], card['priority'], card.get('category'),
                card['title'], card['message'], card.get('messageHindi'), 
                card.get('icon'), card.get('color'),
                card.get('actionType'), card.get('actionAmount'), card.get('actionCategory'),
                card.get('actionDescription'), card.get('expectedSavings'),
                card.get('expectedImpactDays'), card.get('impactDescription'),
                card.get('validFrom'), card.get('validUntil'),
                card.get('isUrgent', False), card.get('daysUntilImpact')
            )
        
        print(f"✅ Saved {len(action_cards)} action cards")
    
    def _print_summary(self, insights: Dict, action_cards: List[Dict]):
        """Print summary of analysis"""
        
        print(f"\n{'='*60}")
        print("📊 FINANCIAL ANALYSIS SUMMARY")
        print(f"{'='*60}")
        
        print(f"\n💰 Income:")
        print(f"  Avg Daily: ₹{insights.get('avgDailyIncome', 0):.0f}")
        print(f"  Stability: {insights.get('incomeStability')} ({insights.get('incomeStabilityScore', 0):.0f}/100)")
        print(f"  Growth: {insights.get('incomeGrowthRate', 0):+.1f}%")
        
        print(f"\n💸 Expenses:")
        print(f"  Avg Daily: ₹{insights.get('avgDailyExpense', 0):.0f}")
        print(f"  Top Category: {insights.get('topExpenseCategory')} (₹{insights.get('topExpenseCategoryAmount', 0):.0f})")
        print(f"  Unnecessary: ₹{insights.get('unnecessarySpendingAmount', 0):.0f}")
        
        print(f"\n💵 Savings:")
        print(f"  Avg Daily: ₹{insights.get('avgDailySavings', 0):.0f}")
        print(f"  Rate: {insights.get('savingsRate', 0):.1f}%")
        print(f"  Consistency: {insights.get('savingsConsistency')}")
        
        print(f"\n⚠️ Risk Assessment:")
        print(f"  Overall: {insights.get('overallRiskLevel')} (Score: {insights.get('riskScore', 0):.0f}/100)")
        print(f"  Grade: {insights.get('financialHealthGrade')}")
        print(f"  Cash Crunch: {insights.get('cashCrunchRisk')}")
        
        if insights.get('riskFactors'):
            print(f"\n  Risk Factors:")
            for factor in insights['riskFactors']:
                print(f"    ❌ {factor}")
        
        if insights.get('strengths'):
            print(f"\n  Strengths:")
            for strength in insights['strengths']:
                print(f"    ✅ {strength}")
        
        print(f"\n📋 Action Cards Generated: {len(action_cards)}")
        for card in action_cards:
            priority_emoji = {
                'urgent': '🔴',
                'high': '🟠',
                'medium': '🟡',
                'low': '🟢'
            }.get(card['priority'], '⚪')
            
            print(f"  {priority_emoji} [{card['priority'].upper()}] {card['title']}")
        
        print(f"\n{'='*60}")
    
    async def run_for_all_users(self):
        """Run planner for all users"""
        
        # Get all user IDs
        user_ids = await self.conn.fetch('SELECT "id" FROM "Customer"')
        
        print(f"\n📊 Running Planner Agent for {len(user_ids)} users...\n")
        
        success_count = 0
        for row in user_ids:
            result = await self.run_for_user(row['id'])
            if result['status'] == 'success':
                success_count += 1
        
        print(f"\n{'='*60}")
        print(f"✅ Completed: {success_count}/{len(user_ids)} users")
        print(f"{'='*60}")



async def main():
    """Main entry point"""
    
    import argparse
    
    parser = argparse.ArgumentParser(description="NuoFunds Planner Agent")
    parser.add_argument('--user-id', type=str, help='Process specific user')
    parser.add_argument('--all', action='store_true', help='Process all users')
    
    args = parser.parse_args()
    
    agent = PlannerAgent()
    
    try:
        await agent.connect()
        
        if args.user_id:
            await agent.run_for_user(args.user_id)
        elif args.all:
            await agent.run_for_all_users()
        else:
            # Default: run for all
            await agent.run_for_all_users()
    
    finally:
        await agent.close()



if __name__ == "__main__":
    # Import FinancialAnalyzer from previous artifact
    asyncio.run(main())