# """
# NuoFunds Notification Generator Agent
# Generates personalized, motivational notifications based on user insights

# Features:
# - Daily morning/evening motivations
# - Weekly summaries
# - Event-based celebrations (savings milestones, streaks)
# - Smart warnings (low balance, upcoming shortfalls)
# - Financial tips and reminders
# - Multi-language support (English + Hindi)
# """

# import os
# import asyncio
# from datetime import datetime, timedelta, time as dt_time
# from typing import Dict, List, Optional
# import asyncpg
# from dotenv import load_dotenv
# import random
# import json
# from decimal import Decimal
# import uuid

# load_dotenv()
# DATABASE_URL = os.getenv("DATABASE_URL")


# def clean_context(data):
#     if isinstance(data, dict):
#         return {k: clean_context(v) for k, v in data.items()}
#     if isinstance(data, list):
#         return [clean_context(v) for v in data]
#     if isinstance(data, Decimal):
#         return float(data)
#     return data


# class NotificationContext:
#     """Holds context data for generating personalized notifications"""
    
#     def __init__(self, user_id: str, insights: Dict, forecasts: List[Dict]):
#         self.user_id = user_id
#         self.insights = insights
#         self.forecasts = forecasts
#         self.user_name = insights.get('userName', 'Friend')


# class NotificationGenerator:
#     """Generates personalized notifications based on user insights"""
    
#     def __init__(self, conn: asyncpg.Connection):
#         self.conn = conn
#         self.notifications = []
    
#     async def generate_for_user(self, user_id: str) -> List[Dict]:
#         """Generate all applicable notifications for a user"""
        
#         print(f"\n🔔 Generating notifications for user {user_id}...")
        
#         # Load user context
#         context = await self._load_user_context(user_id)
        
#         if not context:
#             print("  ⚠️ Insufficient data for notifications")
#             return []
        
#         # Generate different types of notifications
#         await self._generate_daily_motivations(context)
#         await self._generate_celebration_notifications(context)
#         await self._generate_warning_notifications(context)
#         await self._generate_streak_notifications(context)
#         await self._generate_weekly_summary(context)
#         await self._generate_tips_and_reminders(context)
#         await self._generate_milestone_notifications(context)
        
#         print(f"  ✅ Generated {len(self.notifications)} notifications")
        
#         return self.notifications
    
#     async def _load_user_context(self, user_id: str) -> Optional[NotificationContext]:
#         """Load user data needed for notification generation"""
        
#         # Get latest insights
#         insights_row = await self.conn.fetchrow("""
#             SELECT 
#                 ufi.*,
#                 c."name" as "userName",
#                 c."phone"
#             FROM "UserFinancialInsights" ufi
#             JOIN "Customer" c ON c."id" = ufi."userId"
#             WHERE ufi."userId" = $1
#             ORDER BY ufi."analysisDate" DESC
#             LIMIT 1
#         """, user_id)
        
#         if not insights_row:
#             return None
        
#         insights = dict(insights_row)
        
#         # Get upcoming forecasts
#         forecasts = await self.conn.fetch("""
#             SELECT * FROM "Shortfall"
#             WHERE "userId" = $1
#                 AND "forecastDate" >= CURRENT_DATE
#             ORDER BY "forecastDate"
#             LIMIT 14
#         """, user_id)
        
#         return NotificationContext(user_id, insights, [dict(f) for f in forecasts])
    
#     async def _generate_daily_motivations(self, context: NotificationContext):
#         """Generate daily motivational notifications"""
        
#         # Morning motivation (9 AM)
#         morning = {
#             'userId': context.user_id,
#             'category': 'motivation',
#             'notificationType': 'daily',
#             'priority': 'normal',
#             'title': f"Good Morning, {context.user_name}! 🌅",
#             'message': self._get_random_morning_message(context),
#             'titleHindi': f"सुप्रभात, {context.user_name}! 🌅",
#             'messageHindi': self._get_random_morning_message_hindi(context),
#             'icon': '🌅',
#             'color': 'blue',
#             'scheduledFor': self._get_next_scheduled_time(9, 0),
#             'bestTimeToShow': dt_time(9, 0),
#             'expiresAt': self._get_next_scheduled_time(12, 0),
#             'context': {'timeOfDay': 'morning'}
#         }
        
#         self.notifications.append(morning)
        
#         # Evening reflection (9 PM) - only if savings rate is low
#         if (context.insights.get('savingsRate') or 0) < 15:
#             evening = {
#                 'userId': context.user_id,
#                 'category': 'motivation',
#                 'notificationType': 'daily',
#                 'priority': 'low',
#                 'title': "🌙 End of Day Check-in",
#                 'message': "Did you track all your expenses today? Small steps lead to big wins!",
#                 'titleHindi': "🌙 दिन का अंत",
#                 'messageHindi': "क्या आपने आज के सभी खर्च ट्रैक किए? छोटे कदम बड़ी जीत की ओर ले जाते हैं!",
#                 'icon': '🌙',
#                 'color': 'purple',
#                 'scheduledFor': self._get_next_scheduled_time(21, 0),
#                 'bestTimeToShow': dt_time(21, 0),
#                 'expiresAt': self._get_next_scheduled_time(23, 59),
#                 'context': {'timeOfDay': 'evening'}
#             }
            
#             self.notifications.append(evening)
    
#     async def _generate_celebration_notifications(self, context: NotificationContext):
#         """Generate celebration notifications for achievements"""
        
#         savings_rate = context.insights.get('savingsRate', 0)
        
#         # Excellent savings day
#         if savings_rate > 20:
#             amount = context.insights.get('avgDailySavings', 0)
            
#             notif = {
#                 'userId': context.user_id,
#                 'category': 'celebration',
#                 'notificationType': 'event_based',
#                 'priority': 'normal',
#                 'title': "🎉 Great Job Saving!",
#                 'message': f"You're saving {savings_rate:.1f}% of your income! That's ₹{amount:.0f}/day on average.",
#                 'titleHindi': "🎉 बहुत बढ़िया बचत!",
#                 'messageHindi': f"आप अपनी आय का {savings_rate:.1f}% बचा रहे हैं! यह औसतन ₹{amount:.0f}/दिन है।",
#                 'icon': '🎉',
#                 'color': 'green',
#                 'scheduledFor': self._get_next_scheduled_time(19, 0),
#                 'bestTimeToShow': dt_time(19, 0),
#                 'validUntil': datetime.now() + timedelta(days=2),
#                 'context': {
#                     'achievement': 'good_savings',
#                     'savings_rate': savings_rate,
#                     'amount': amount
#                 },
#                 'isInteractive': True,
#                 'actionButton': 'View Details',
#                 'actionUrl': '/insights'
#             }
            
#             self.notifications.append(notif)
        
#         # Income growth celebration
#         growth_rate = context.insights.get('incomeGrowthRate', 0)
#         if growth_rate > 10:
#             notif = {
#                 'userId': context.user_id,
#                 'category': 'celebration',
#                 'notificationType': 'event_based',
#                 'priority': 'normal',
#                 'title': "📈 Income Growing!",
#                 'message': f"Your income increased by {growth_rate:.1f}% this month! Keep up the great work!",
#                 'titleHindi': "📈 आय बढ़ रही है!",
#                 'messageHindi': f"इस महीने आपकी आय {growth_rate:.1f}% बढ़ी! बढ़िया काम जारी रखें!",
#                 'icon': '📈',
#                 'color': 'green',
#                 'scheduledFor': self._get_next_scheduled_time(18, 0),
#                 'context': {'growth_rate': growth_rate}
#             }
            
#             self.notifications.append(notif)
    
#     async def _generate_warning_notifications(self, context: NotificationContext):
#         """Generate warning notifications for risks"""
        
#         # Low balance warning
#         lowest_balance = context.insights.get('lowestBalance', 1000)
#         if lowest_balance < 500:
#             notif = {
#                 'userId': context.user_id,
#                 'category': 'warning',
#                 'notificationType': 'event_based',
#                 'priority': 'high',
#                 'title': "⚠️ Balance Getting Low",
#                 'message': f"Your balance dropped to ₹{lowest_balance:.0f}. Plan your expenses carefully.",
#                 'titleHindi': "⚠️ बैलेंस कम हो रहा है",
#                 'messageHindi': f"आपका बैलेंस ₹{lowest_balance:.0f} तक गिर गया। सावधानी से खर्च करें।",
#                 'icon': '⚠️',
#                 'color': 'red',
#                 'scheduledFor': datetime.now() + timedelta(minutes=30),
#                 'priority': 'urgent' if lowest_balance < 200 else 'high',
#                 'validUntil': datetime.now() + timedelta(days=1),
#                 'context': {'lowest_balance': lowest_balance},
#                 'isInteractive': True,
#                 'actionButton': 'See Tips',
#                 'actionUrl': '/tips/emergency'
#             }
            
#             self.notifications.append(notif)
        
#         # Upcoming shortfall warning
#         shortfall_days = context.insights.get('predictedShortfallDays', 0)
#         if shortfall_days > 0:
#             next_date = context.insights.get('nextLowBalanceDate')
#             days_until = (next_date - datetime.now().date()).days if next_date else 7
            
#             notif = {
#                 'userId': context.user_id,
#                 'category': 'warning',
#                 'notificationType': 'event_based',
#                 'priority': 'high',
#                 'title': "📅 Heads Up!",
#                 'message': f"You might face a cash shortage in {days_until} days. Let's plan ahead!",
#                 'titleHindi': "📅 ध्यान दें!",
#                 'messageHindi': f"{days_until} दिनों में पैसों की कमी हो सकती है। पहले से योजना बनाएं!",
#                 'icon': '📅',
#                 'color': 'orange',
#                 'scheduledFor': self._get_next_scheduled_time(10, 0),
#                 'validUntil': next_date if next_date else datetime.now() + timedelta(days=7),
#                 'context': {
#                     'days_until': days_until,
#                     'shortfall_amount': context.insights.get('predictedShortfallAmount', 0)
#                 },
#                 'isInteractive': True,
#                 'actionButton': 'Make Plan',
#                 'actionUrl': '/action-cards'
#             }
            
#             self.notifications.append(notif)
        
#         # High spending alert
#         unnecessary = context.insights.get('unnecessarySpendingAmount', 0)
#         if unnecessary > 1000:
#             notif = {
#                 'userId': context.user_id,
#                 'category': 'warning',
#                 'notificationType': 'event_based',
#                 'priority': 'medium',
#                 'title': "🛑 Spending Alert",
#                 'message': f"You spent ₹{unnecessary:.0f} on non-essentials this month. Consider cutting back!",
#                 'titleHindi': "🛑 खर्च अलर्ट",
#                 'messageHindi': f"इस महीने गैर-ज़रूरी चीज़ों पर ₹{unnecessary:.0f} खर्च हुए। कम करने पर विचार करें!",
#                 'icon': '🛑',
#                 'color': 'orange',
#                 'scheduledFor': self._get_next_scheduled_time(12, 0),
#                 'context': {'unnecessary_spending': unnecessary}
#             }
            
#             self.notifications.append(notif)
    
#     async def _generate_streak_notifications(self, context: NotificationContext):
#         """Generate notifications for savings streaks"""
        
#         # Check if user has an active savings streak
#         streak = await self.conn.fetchrow("""
#             SELECT * FROM "MotivationStreak"
#             WHERE "userId" = $1
#                 AND "streakType" = 'savings'
#                 AND "isActive" = TRUE
#             ORDER BY "updatedAt" DESC
#             LIMIT 1
#         """, context.user_id)
        
#         if streak:
#             current_streak = streak['currentStreak']
            
#             # Milestone notifications (7, 14, 30, 60, 90 days)
#             milestones = [7, 14, 30, 60, 90]
            
#             if current_streak in milestones:
#                 notif = {
#                     'userId': context.user_id,
#                     'category': 'milestone',
#                     'notificationType': 'event_based',
#                     'priority': 'high',
#                     'title': f"🔥 {current_streak} Day Streak!",
#                     'message': f"You've saved money for {current_streak} days straight! Amazing discipline! 💪",
#                     'titleHindi': f"🔥 {current_streak} दिन की स्ट्रीक!",
#                     'messageHindi': f"आप {current_streak} दिनों से लगातार पैसे बचा रहे हैं! शानदार अनुशासन! 💪",
#                     'icon': '🔥',
#                     'color': 'green',
#                     'scheduledFor': self._get_next_scheduled_time(19, 0),
#                     'context': {
#                         'streak_days': current_streak,
#                         'milestone': True
#                     },
#                     'isInteractive': True,
#                     'actionButton': 'Share Achievement',
#                     'actionUrl': '/share/streak'
#                 }
                
#                 self.notifications.append(notif)
    
#     async def _generate_weekly_summary(self, context: NotificationContext):
#         """Generate weekly summary notification (Monday morning)"""
        
#         # Only schedule for Monday
#         next_monday = self._get_next_weekday(0)  # 0 = Monday
        
#         avg_income = context.insights.get('avgDailyIncome', 0) * 7
#         avg_expense = context.insights.get('avgDailyExpense', 0) * 7
#         avg_savings = context.insights.get('avgDailySavings', 0) * 7
        
#         notif = {
#             'userId': context.user_id,
#             'category': 'reminder',
#             'notificationType': 'weekly',
#             'priority': 'normal',
#             'title': "📊 Your Week Ahead",
#             'message': f"Expected: Earn ₹{avg_income:.0f}, Spend ₹{avg_expense:.0f}, Save ₹{avg_savings:.0f}",
#             'titleHindi': "📊 आगामी सप्ताह",
#             'messageHindi': f"अनुमान: कमाई ₹{avg_income:.0f}, खर्च ₹{avg_expense:.0f}, बचत ₹{avg_savings:.0f}",
#             'icon': '📊',
#             'color': 'blue',
#             'scheduledFor': next_monday.replace(hour=9, minute=0),
#             'bestTimeToShow': dt_time(9, 0),
#             'validUntil': next_monday + timedelta(hours=12),
#             'context': {
#                 'weekly_income': avg_income,
#                 'weekly_expense': avg_expense,
#                 'weekly_savings': avg_savings
#             },
#             'isInteractive': True,
#             'actionButton': 'View Forecast',
#             'actionUrl': '/forecast'
#         }
        
#         self.notifications.append(notif)
    
#     async def _generate_tips_and_reminders(self, context: NotificationContext):
#         """Generate helpful tips and reminders"""
        
#         top_category = context.insights.get('topExpenseCategory', 'food')
#         top_amount = context.insights.get('topExpenseCategoryAmount', 0)
        
#         # Category-specific tips
#         tips = {
#             'food': {
#                 'en': "💡 Try packing lunch from home. You can save ₹100-150 per day!",
#                 'hi': "💡 घर से खाना लेकर जाएं। रोज़ ₹100-150 बचा सकते हैं!"
#             },
#             'fuel': {
#                 'en': "💡 Check tire pressure regularly. Proper inflation saves 3-5% fuel!",
#                 'hi': "💡 टायर प्रेशर नियमित जांचें। सही दबाव से 3-5% फ्यूल बचता है!"
#             },
#             'travel': {
#                 'en': "💡 Consider carpooling or public transport for non-work trips!",
#                 'hi': "💡 गैर-काम की यात्राओं के लिए कारपूलिंग या सार्वजनिक परिवहन पर विचार करें!"
#             },
#             'shopping': {
#                 'en': "💡 Make a list before shopping. It reduces impulse buys by 40%!",
#                 'hi': "💡 खरीदारी से पहले सूची बनाएं। यह आवेगपूर्ण खरीदारी 40% कम करता है!"
#             }
#         }
        
#         tip_data = tips.get(top_category, tips['food'])
        
#         notif = {
#             'userId': context.user_id,
#             'category': 'tip',
#             'notificationType': 'daily',
#             'priority': 'low',
#             'title': "💡 Money Saving Tip",
#             'message': tip_data['en'],
#             'titleHindi': "💡 पैसे बचाने का टिप",
#             'messageHindi': tip_data['hi'],
#             'icon': '💡',
#             'color': 'yellow',
#             'scheduledFor': self._get_next_scheduled_time(12, 0),
#             'bestTimeToShow': dt_time(12, 0),
#             'expiresAt': self._get_next_scheduled_time(15, 0),
#             'context': {
#                 'tip_category': top_category,
#                 'spending_amount': top_amount
#             }
#         }
        
#         self.notifications.append(notif)
    
#     async def _generate_milestone_notifications(self, context: NotificationContext):
#         """Generate milestone celebration notifications"""
        
#         total_savings = context.insights.get('totalSavingsLast30Days', 0)
        
#         # Savings milestone
#         milestones = [1000, 2000, 5000, 10000, 20000, 50000]
        
#         for milestone in milestones:
#             if abs(total_savings - milestone) < 500:  # Within ₹500 of milestone
#                 notif = {
#                     'userId': context.user_id,
#                     'category': 'milestone',
#                     'notificationType': 'event_based',
#                     'priority': 'normal',
#                     'title': f"🎯 Almost There!",
#                     'message': f"You're ₹{abs(milestone - total_savings):.0f} away from saving ₹{milestone}!",
#                     'titleHindi': f"🎯 लगभग पहुंच गए!",
#                     'messageHindi': f"₹{milestone} बचत से सिर्फ ₹{abs(milestone - total_savings):.0f} दूर!",
#                     'icon': '🎯',
#                     'color': 'green',
#                     'scheduledFor': self._get_next_scheduled_time(20, 0),
#                     'context': {
#                         'milestone': milestone,
#                         'current_savings': total_savings,
#                         'remaining': abs(milestone - total_savings)
#                     }
#                 }
                
#                 self.notifications.append(notif)
#                 break  # Only one milestone notification
    
#     def _get_random_morning_message(self, context: NotificationContext) -> str:
#         """Get random personalized morning message"""
        
#         messages = [
#             "Start your day right! Remember to track your expenses today.",
#             f"Good to see you, {context.user_name}! Let's make today count!",
#             "New day, new opportunities to save! You've got this! 💪",
#             "Track your spending today and watch your savings grow! 🌱",
#             f"Ready for a great day, {context.user_name}? Let's stay on budget!"
#         ]
        
#         # Personalize based on risk level
#         risk_level = context.insights.get('overallRiskLevel', 'medium')
        
#         if risk_level == 'high' or risk_level == 'critical':
#             messages.append("Today's focus: Control spending and plan ahead!")
#         elif risk_level == 'low':
#             messages.append("You're doing great! Keep up the excellent work!")
        
#         return random.choice(messages)
    
#     def _get_random_morning_message_hindi(self, context: NotificationContext) -> str:
#         """Get random personalized morning message in Hindi"""
        
#         messages = [
#             "अपना दिन अच्छे से शुरू करें! आज अपने खर्चों पर नज़र रखें।",
#             f"आपको देखकर अच्छा लगा, {context.user_name}! आज का दिन बेहतरीन बनाएं!",
#             "नया दिन, बचत के नए अवसर! आप कर सकते हैं! 💪",
#             "आज खर्च ट्रैक करें और अपनी बचत बढ़ते देखें! 🌱",
#         ]
        
#         return random.choice(messages)
    
#     def _get_next_scheduled_time(self, hour: int, minute: int) -> datetime:
#         """Get next occurrence of specified time"""
#         now = datetime.now()
#         scheduled = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        
#         if scheduled < now:
#             scheduled += timedelta(days=1)
        
#         return scheduled
    
#     def _get_next_weekday(self, weekday: int) -> datetime:
#         """Get next occurrence of specified weekday (0=Monday, 6=Sunday)"""
#         now = datetime.now()
#         days_ahead = weekday - now.weekday()
        
#         if days_ahead <= 0:
#             days_ahead += 7
        
#         return now + timedelta(days=days_ahead)


# class NotificationScheduler:
#     """Schedules and saves notifications to database"""
    
#     def __init__(self, conn: asyncpg.Connection):
#         self.conn = conn
    
#     # async def schedule_notifications(self, notifications: List[Dict]):
#     #     """Save notifications to database"""
        
#     #     print(f"\n💾 Scheduling {len(notifications)} notifications...")
        
#     #     saved_count = 0
        
#     #     for notif in notifications:
#     #         try:
#     #             # Check if similar notification already exists (avoid duplicates)
#     #             exists = await self._check_duplicate(notif)
                
#     #             if exists:
#     #                 continue
#     #             ctx = notif.get('context')
#     #             ctx = clean_context(ctx) if ctx else None
#     #             await self.conn.execute("""
#     #                 INSERT INTO "UserNotification" (
#     #                     "userId", "category", "notificationType", "priority",
#     #                     "title", "message", "titleHindi", "messageHindi",
#     #                     "icon", "color",
#     #                     "scheduledFor", "bestTimeToShow", "expiresAt",
#     #                     "validFrom", "validUntil",
#     #                     "context", "isInteractive", "actionButton", "actionUrl",
#     #                     "channels"
#     #                 ) VALUES (
#     #                     $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13,
#     #                     $14, $15, $16, $17, $18, $19, $20
#     #                 )
#     #             """,
#     #                 notif['userId'],
#     #                 notif['category'],
#     #                 notif['notificationType'],
#     #                 notif['priority'],
#     #                 notif['title'],
#     #                 notif['message'],
#     #                 notif.get('titleHindi'),
#     #                 notif.get('messageHindi'),
#     #                 notif.get('icon'),
#     #                 notif.get('color'),
#     #                 notif['scheduledFor'],
#     #                 notif.get('bestTimeToShow'),
#     #                 notif.get('expiresAt'),
#     #                 notif.get('validFrom', datetime.now()),
#     #                 notif.get('validUntil'),
#     #                 json.dumps(ctx),
#     #                 notif.get('isInteractive', False),
#     #                 notif.get('actionButton'),
#     #                 notif.get('actionUrl'),
#     #                 ['in_app', 'push']  # Default channels
#     #             )
                
#     #             saved_count += 1
                
#     #         except Exception as e:
#     #             print(f"  ❌ Error saving notification: {e}")
        
#     #     print(f"  ✅ Scheduled {saved_count} notifications")
    
#     async def schedule_notifications(self, notifications: List[Dict]):
#         """Save notifications to database"""
        
#         print(f"\n💾 Scheduling {len(notifications)} notifications.")
        
#         saved_count = 0
        
#         for notif in notifications:
#             try:
#                 # Check if similar notification already exists (avoid duplicates)
#                 exists = await self._check_duplicate(notif)
#                 if exists:
#                     continue

#                 # ✅ generate id for this notification
#                 notif_id = str(uuid.uuid4())

#                 ctx = notif.get('context')
#                 ctx = clean_context(ctx) if ctx else None

#                 await self.conn.execute("""
#                     INSERT INTO "UserNotification" (
#                         "id",
#                         "userId", "category", "notificationType", "priority",
#                         "title", "message", "titleHindi", "messageHindi",
#                         "icon", "color",
#                         "scheduledFor", "bestTimeToShow", "expiresAt",
#                         "validFrom", "validUntil",
#                         "context", "isInteractive", "actionButton", "actionUrl",
#                         "channels"
#                     ) VALUES (
#                         $1,
#                         $2, $3, $4, $5, $6, $7, $8, $9, $10,
#                         $11, $12, $13, $14, $15, $16,
#                         $17, $18, $19, $20, $21
#                     )
#                 """,
#                     notif_id,  # $1
#                     notif['userId'],                # $2
#                     notif['category'],              # $3
#                     notif['notificationType'],      # $4
#                     notif['priority'],              # $5
#                     notif['title'],                 # $6
#                     notif['message'],               # $7
#                     notif.get('titleHindi'),        # $8
#                     notif.get('messageHindi'),      # $9
#                     notif.get('icon'),              # $10
#                     notif.get('color'),             # $11
#                     notif['scheduledFor'],          # $12
#                     notif.get('bestTimeToShow'),    # $13
#                     notif.get('expiresAt'),         # $14
#                     notif.get('validFrom', datetime.now()),  # $15
#                     notif.get('validUntil'),        # $16
#                     json.dumps(ctx),                # $17
#                     notif.get('isInteractive', False),  # $18
#                     notif.get('actionButton'),      # $19
#                     notif.get('actionUrl'),         # $20
#                     ['in_app', 'push']              # $21
#                 )
                
#                 saved_count += 1

#             except Exception as e:
#                 print(f"  ❌ Error saving notification: {e}")
        
#         print(f"  ✅ Scheduled {saved_count} notifications")



#     async def _check_duplicate(self, notif: Dict) -> bool:
#         """Check if similar notification already exists"""
        
#         # Check for same category + scheduled time within 1 hour
#         exists = await self.conn.fetchval("""
#             SELECT EXISTS(
#                 SELECT 1 FROM "UserNotification"
#                 WHERE "userId" = $1
#                     AND "category" = $2
#                     AND "status" IN ('scheduled', 'sent')
#                     AND ABS(EXTRACT(EPOCH FROM ("scheduledFor" - $3))) < 3600
#             )
#         """,
#             notif['userId'],
#             notif['category'],
#             notif['scheduledFor']
#         )
        
#         return exists

# class NotificationOrchestrator:
#     """Main orchestrator for notification system"""
    
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
    
#     async def generate_for_user(self, user_id: str):
#         """Generate notifications for one user"""
        
#         print(f"\n{'='*60}")
#         print(f"🔔 NOTIFICATION GENERATOR - User: {user_id}")
#         print(f"{'='*60}")
        
#         try:
#             # Generate notifications
#             generator = NotificationGenerator(self.conn)
#             notifications = await generator.generate_for_user(user_id)
            
#             if not notifications:
#                 print("  ℹ️ No new notifications to generate")
#                 return
            
#             # Schedule notifications
#             scheduler = NotificationScheduler(self.conn)
#             await scheduler.schedule_notifications(notifications)
            
#             # Print summary
#             self._print_summary(notifications)
            
#             return {
#                 'status': 'success',
#                 'count': len(notifications)
#             }
            
#         except Exception as e:
#             print(f"❌ Error: {e}")
#             import traceback
#             traceback.print_exc()
#             return {'status': 'error', 'message': str(e)}
    
#     async def generate_for_all_users(self):
#         """Generate notifications for all users"""
        
#         user_ids = await self.conn.fetch('SELECT "id" FROM "Customer"')
        
#         print(f"\n🔔 Generating notifications for {len(user_ids)} users...\n")
        
#         total_notifications = 0
        
#         for row in user_ids:
#             result = await self.generate_for_user(row['id'])
#             if result and result['status'] == 'success':
#                 total_notifications += result.get('count', 0)
        
#         print(f"\n{'='*60}")
#         print(f"✅ Total Notifications Scheduled: {total_notifications}")
#         print(f"{'='*60}")
    
    # async def send_due_notifications(self):
    #     """Send notifications that are due now"""
        
    #     print("\n📤 Sending due notifications...")
        
    #     # Get notifications ready to send
    #     due_notifications = await self.conn.fetch("""
    #         SELECT * FROM "v_NotificationsReadyToSend"
    #         LIMIT 100
    #     """)
        
    #     if not due_notifications:
    #         print("  ℹ️ No notifications due right now")
    #         return
        
    #     print(f"  📨 Found {len(due_notifications)} notifications to send")
        
    #     sent_count = 0
        
    #     for notif in due_notifications:
    #         try:
    #             # Mark as sent (in production, actually send via push/SMS/email)
    #             await self.conn.execute("""
    #                 UPDATE "UserNotification"
    #                 SET "status" = 'sent',
    #                     "sentAt" = CURRENT_TIMESTAMP,
    #                     "deliveredChannels" = $1
    #                 WHERE "id" = $2
    #             """, ['in_app'], notif['id'])
                
    #             sent_count += 1
                
        #         # Log delivery
        #         print(f"  ✉️ Sent: {notif['title']} → {notif['userName']}")
                
        #     except Exception as e:
        #         print(f"  ❌ Failed to send: {e}")
        
        # print(f"\n  ✅ Sent {sent_count}/{len(due_notifications)} notifications")
    
    # def _print_summary(self, notifications: List[Dict]):
    #     """Print summary of generated notifications"""
        
    #     # Group by category
    #     by_category = {}
    #     by_priority = {}
        
    #     for notif in notifications:
    #         cat = notif['category']
    #         pri = notif['priority']
            
    #         by_category[cat] = by_category.get(cat, 0) + 1
    #         by_priority[pri] = by_priority.get(pri, 0) + 1
        
    #     print(f"\n📊 Notification Summary:")
    #     print(f"\n  By Category:")
    #     for cat, count in sorted(by_category.items()):
    #         print(f"    {cat:15s}: {count}")
        
    #     print(f"\n  By Priority:")
    #     for pri, count in sorted(by_priority.items()):
    #         emoji = {'urgent': '🔴', 'high': '🟠', 'normal': '🟡', 'low': '🟢'}.get(pri, '⚪')
    #         print(f"    {emoji} {pri:10s}: {count}")


# async def main():
#     """Main entry point"""
    
#     import argparse
    
#     parser = argparse.ArgumentParser(description="NuoFunds Notification System")
#     parser.add_argument('--user-id', type=str, help='Generate for specific user')
#     parser.add_argument('--all', action='store_true', help='Generate for all users')
#     parser.add_argument('--send', action='store_true', help='Send due notifications')
    
#     args = parser.parse_args()
    
#     orchestrator = NotificationOrchestrator()
    
#     try:
#         await orchestrator.connect()
        
#         if args.send:
#             await orchestrator.send_due_notifications()
#         elif args.user_id:
#             await orchestrator.generate_for_user(args.user_id)
#         elif args.all:
#             await orchestrator.generate_for_all_users()
#         else:
#             # Default: generate for all
#             await orchestrator.generate_for_all_users()
    
#     finally:
#         await orchestrator.close()


# if __name__ == "__main__":
#     asyncio.run(main())











"""
NuoFunds Notification Generator Agent
Generates personalized, motivational notifications based on user insights

Features:
- Daily morning/evening motivations
- Weekly summaries
- Event-based celebrations (savings milestones, streaks)
- Smart warnings (low balance, upcoming shortfalls)
- Financial tips and reminders
- Multi-language support (English + Hindi)
"""

import os
import asyncio
from datetime import datetime, timedelta, time as dt_time
from typing import Dict, List, Optional
import asyncpg
from dotenv import load_dotenv
import random
import json
from decimal import Decimal
import uuid

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")


def clean_context(data):
    if isinstance(data, dict):
        return {k: clean_context(v) for k, v in data.items()}
    if isinstance(data, list):
        return [clean_context(v) for v in data]
    if isinstance(data, Decimal):
        return float(data)
    return data


def safe_number(value, default=0):
    """Safely convert value to number, handling None and other non-numeric types"""
    if value is None:
        return default
    try:
        return float(value)
    except (ValueError, TypeError):
        return default


class NotificationContext:
    """Holds context data for generating personalized notifications"""
    
    def __init__(self, user_id: str, insights: Dict, forecasts: List[Dict]):
        self.user_id = user_id
        self.insights = insights
        self.forecasts = forecasts
        self.user_name = insights.get('userName', 'Friend')
    
    def get_number(self, key: str, default=0) -> float:
        """Safely get a numeric value from insights"""
        return safe_number(self.insights.get(key), default)


class NotificationGenerator:
    """Generates personalized notifications based on user insights"""
    
    def __init__(self, conn: asyncpg.Connection):
        self.conn = conn
        self.notifications = []
    
    async def generate_for_user(self, user_id: str) -> List[Dict]:
        """Generate all applicable notifications for a user"""
        
        print(f"\n📢 Generating notifications for user {user_id}...")
        
        # Load user context
        context = await self._load_user_context(user_id)
        
        if not context:
            print("  ⚠️ Insufficient data for notifications")
            return []
        
        # Generate different types of notifications
        await self._generate_daily_motivations(context)
        await self._generate_celebration_notifications(context)
        await self._generate_warning_notifications(context)
        await self._generate_streak_notifications(context)
        await self._generate_weekly_summary(context)
        await self._generate_tips_and_reminders(context)
        await self._generate_milestone_notifications(context)
        
        print(f"  ✅ Generated {len(self.notifications)} notifications")
        
        return self.notifications
    
    async def _load_user_context(self, user_id: str) -> Optional[NotificationContext]:
        """Load user data needed for notification generation"""
        
        # Get latest insights
        insights_row = await self.conn.fetchrow("""
            SELECT 
                ufi.*,
                c."name" as "userName",
                c."phone"
            FROM "UserFinancialInsights" ufi
            JOIN "Customer" c ON c."id" = ufi."userId"
            WHERE ufi."userId" = $1
            ORDER BY ufi."analysisDate" DESC
            LIMIT 1
        """, user_id)
        
        if not insights_row:
            return None
        
        insights = dict(insights_row)
        
        # Get upcoming forecasts
        forecasts = await self.conn.fetch("""
            SELECT * FROM "Shortfall"
            WHERE "userId" = $1
                AND "forecastDate" >= CURRENT_DATE
            ORDER BY "forecastDate"
            LIMIT 14
        """, user_id)
        
        return NotificationContext(user_id, insights, [dict(f) for f in forecasts])
    
    async def _generate_daily_motivations(self, context: NotificationContext):
        """Generate daily motivational notifications"""
        
        # Morning motivation (9 AM)
        morning = {
            'userId': context.user_id,
            'category': 'motivation',
            'notificationType': 'daily',
            'priority': 'normal',
            'title': f"Good Morning, {context.user_name}! 🌅",
            'message': self._get_random_morning_message(context),
            'titleHindi': f"सुप्रभात, {context.user_name}! 🌅",
            'messageHindi': self._get_random_morning_message_hindi(context),
            'icon': '🌅',
            'color': 'blue',
            'scheduledFor': self._get_next_scheduled_time(9, 0),
            'bestTimeToShow': dt_time(9, 0),
            'expiresAt': self._get_next_scheduled_time(12, 0),
            'context': {'timeOfDay': 'morning'}
        }
        
        self.notifications.append(morning)
        
        # Evening reflection (9 PM) - only if savings rate is low
        if context.get_number('savingsRate') < 15:
            evening = {
                'userId': context.user_id,
                'category': 'motivation',
                'notificationType': 'daily',
                'priority': 'low',
                'title': "🌙 End of Day Check-in",
                'message': "Did you track all your expenses today? Small steps lead to big wins!",
                'titleHindi': "🌙 दिन का अंत",
                'messageHindi': "क्या आपने आज के सभी खर्च ट्रैक किए? छोटे कदम बड़ी जीत की ओर ले जाते हैं!",
                'icon': '🌙',
                'color': 'purple',
                'scheduledFor': self._get_next_scheduled_time(21, 0),
                'bestTimeToShow': dt_time(21, 0),
                'expiresAt': self._get_next_scheduled_time(23, 59),
                'context': {'timeOfDay': 'evening'}
            }
            
            self.notifications.append(evening)
    
    async def _generate_celebration_notifications(self, context: NotificationContext):
        """Generate celebration notifications for achievements"""
        
        savings_rate = context.get_number('savingsRate')
        
        # Excellent savings day
        if savings_rate > 20:
            amount = context.get_number('avgDailySavings')
            
            notif = {
                'userId': context.user_id,
                'category': 'celebration',
                'notificationType': 'event_based',
                'priority': 'normal',
                'title': "🎉 Great Job Saving!",
                'message': f"You're saving {savings_rate:.1f}% of your income! That's ₹{amount:.0f}/day on average.",
                'titleHindi': "🎉 बहुत बढ़िया बचत!",
                'messageHindi': f"आप अपनी आय का {savings_rate:.1f}% बचा रहे हैं! यह औसतन ₹{amount:.0f}/दिन है।",
                'icon': '🎉',
                'color': 'green',
                'scheduledFor': self._get_next_scheduled_time(19, 0),
                'bestTimeToShow': dt_time(19, 0),
                'validUntil': datetime.now() + timedelta(days=2),
                'context': {
                    'achievement': 'good_savings',
                    'savings_rate': savings_rate,
                    'amount': amount
                },
                'isInteractive': True,
                'actionButton': 'View Details',
                'actionUrl': '/insights'
            }
            
            self.notifications.append(notif)
        
        # Income growth celebration
        growth_rate = context.get_number('incomeGrowthRate')
        if growth_rate > 10:
            notif = {
                'userId': context.user_id,
                'category': 'celebration',
                'notificationType': 'event_based',
                'priority': 'normal',
                'title': "📈 Income Growing!",
                'message': f"Your income increased by {growth_rate:.1f}% this month! Keep up the great work!",
                'titleHindi': "📈 आय बढ़ रही है!",
                'messageHindi': f"इस महीने आपकी आय {growth_rate:.1f}% बढ़ी! बढ़िया काम जारी रखें!",
                'icon': '📈',
                'color': 'green',
                'scheduledFor': self._get_next_scheduled_time(18, 0),
                'context': {'growth_rate': growth_rate}
            }
            
            self.notifications.append(notif)
    
    async def _generate_warning_notifications(self, context: NotificationContext):
        """Generate warning notifications for risks"""
        
        # Low balance warning
        lowest_balance = context.get_number('lowestBalance', 1000)
        if lowest_balance < 500:
            notif = {
                'userId': context.user_id,
                'category': 'warning',
                'notificationType': 'event_based',
                'priority': 'high',
                'title': "⚠️ Balance Getting Low",
                'message': f"Your balance dropped to ₹{lowest_balance:.0f}. Plan your expenses carefully.",
                'titleHindi': "⚠️ बैलेंस कम हो रहा है",
                'messageHindi': f"आपका बैलेंस ₹{lowest_balance:.0f} तक गिर गया। सावधानी से खर्च करें।",
                'icon': '⚠️',
                'color': 'red',
                'scheduledFor': datetime.now() + timedelta(minutes=30),
                'priority': 'urgent' if lowest_balance < 200 else 'high',
                'validUntil': datetime.now() + timedelta(days=1),
                'context': {'lowest_balance': lowest_balance},
                'isInteractive': True,
                'actionButton': 'See Tips',
                'actionUrl': '/tips/emergency'
            }
            
            self.notifications.append(notif)
        
        # Upcoming shortfall warning
        shortfall_days = context.get_number('predictedShortfallDays')
        if shortfall_days > 0:
            next_date = context.insights.get('nextLowBalanceDate')
            days_until = (next_date - datetime.now().date()).days if next_date else 7
            
            notif = {
                'userId': context.user_id,
                'category': 'warning',
                'notificationType': 'event_based',
                'priority': 'high',
                'title': "📅 Heads Up!",
                'message': f"You might face a cash shortage in {days_until} days. Let's plan ahead!",
                'titleHindi': "📅 ध्यान दें!",
                'messageHindi': f"{days_until} दिनों में पैसों की कमी हो सकती है। पहले से योजना बनाएं!",
                'icon': '📅',
                'color': 'orange',
                'scheduledFor': self._get_next_scheduled_time(10, 0),
                'validUntil': next_date if next_date else datetime.now() + timedelta(days=7),
                'context': {
                    'days_until': days_until,
                    'shortfall_amount': context.get_number('predictedShortfallAmount')
                },
                'isInteractive': True,
                'actionButton': 'Make Plan',
                'actionUrl': '/action-cards'
            }
            
            self.notifications.append(notif)
        
        # High spending alert
        unnecessary = context.get_number('unnecessarySpendingAmount')
        if unnecessary > 1000:
            notif = {
                'userId': context.user_id,
                'category': 'warning',
                'notificationType': 'event_based',
                'priority': 'medium',
                'title': "🛑 Spending Alert",
                'message': f"You spent ₹{unnecessary:.0f} on non-essentials this month. Consider cutting back!",
                'titleHindi': "🛑 खर्च अलर्ट",
                'messageHindi': f"इस महीने गैर-ज़रूरी चीज़ों पर ₹{unnecessary:.0f} खर्च हुआ। कम करने पर विचार करें!",
                'icon': '🛑',
                'color': 'orange',
                'scheduledFor': self._get_next_scheduled_time(12, 0),
                'context': {'unnecessary_spending': unnecessary}
            }
            
            self.notifications.append(notif)
    
    async def _generate_streak_notifications(self, context: NotificationContext):
        """Generate notifications for savings streaks"""
        
        # Check if user has an active savings streak
        streak = await self.conn.fetchrow("""
            SELECT * FROM "MotivationStreak"
            WHERE "userId" = $1
                AND "streakType" = 'savings'
                AND "isActive" = TRUE
            ORDER BY "updatedAt" DESC
            LIMIT 1
        """, context.user_id)
        
        if streak:
            current_streak = streak['currentStreak']
            
            # Milestone notifications (7, 14, 30, 60, 90 days)
            milestones = [7, 14, 30, 60, 90]
            
            if current_streak in milestones:
                notif = {
                    'userId': context.user_id,
                    'category': 'milestone',
                    'notificationType': 'event_based',
                    'priority': 'high',
                    'title': f"🔥 {current_streak} Day Streak!",
                    'message': f"You've saved money for {current_streak} days straight! Amazing discipline! 💪",
                    'titleHindi': f"🔥 {current_streak} दिन की स्ट्रीक!",
                    'messageHindi': f"आप {current_streak} दिनों से लगातार पैसे बचा रहे हैं! शानदार अनुशासन! 💪",
                    'icon': '🔥',
                    'color': 'green',
                    'scheduledFor': self._get_next_scheduled_time(19, 0),
                    'context': {
                        'streak_days': current_streak,
                        'milestone': True
                    },
                    'isInteractive': True,
                    'actionButton': 'Share Achievement',
                    'actionUrl': '/share/streak'
                }
                
                self.notifications.append(notif)
    
    async def _generate_weekly_summary(self, context: NotificationContext):
        """Generate weekly summary notification (Monday morning)"""
        
        # Only schedule for Monday
        next_monday = self._get_next_weekday(0)  # 0 = Monday
        
        avg_income = context.get_number('avgDailyIncome') * 7
        avg_expense = context.get_number('avgDailyExpense') * 7
        avg_savings = context.get_number('avgDailySavings') * 7
        
        notif = {
            'userId': context.user_id,
            'category': 'reminder',
            'notificationType': 'weekly',
            'priority': 'normal',
            'title': "📊 Your Week Ahead",
            'message': f"Expected: Earn ₹{avg_income:.0f}, Spend ₹{avg_expense:.0f}, Save ₹{avg_savings:.0f}",
            'titleHindi': "📊 आगामी सप्ताह",
            'messageHindi': f"अनुमान: कमाई ₹{avg_income:.0f}, खर्च ₹{avg_expense:.0f}, बचत ₹{avg_savings:.0f}",
            'icon': '📊',
            'color': 'blue',
            'scheduledFor': next_monday.replace(hour=9, minute=0),
            'bestTimeToShow': dt_time(9, 0),
            'validUntil': next_monday + timedelta(hours=12),
            'context': {
                'weekly_income': avg_income,
                'weekly_expense': avg_expense,
                'weekly_savings': avg_savings
            },
            'isInteractive': True,
            'actionButton': 'View Forecast',
            'actionUrl': '/forecast'
        }
        
        self.notifications.append(notif)
    
    async def _generate_tips_and_reminders(self, context: NotificationContext):
        """Generate helpful tips and reminders"""
        
        top_category = context.insights.get('topExpenseCategory', 'food')
        top_amount = context.get_number('topExpenseCategoryAmount')
        
        # Category-specific tips
        tips = {
            'food': {
                'en': "💡 Try packing lunch from home. You can save ₹100-150 per day!",
                'hi': "💡 घर से खाना लेकर जाएं। रोज़ ₹100-150 बचा सकते हैं!"
            },
            'fuel': {
                'en': "💡 Check tire pressure regularly. Proper inflation saves 3-5% fuel!",
                'hi': "💡 टायर प्रेशर नियमित जांचें। सही दबाव से 3-5% फ्यूल बचता है!"
            },
            'travel': {
                'en': "💡 Consider carpooling or public transport for non-work trips!",
                'hi': "💡 गैर-काम की यात्राओं के लिए कारपूलिंग या सार्वजनिक परिवहन पर विचार करें!"
            },
            'shopping': {
                'en': "💡 Make a list before shopping. It reduces impulse buys by 40%!",
                'hi': "💡 खरीदारी से पहले सूची बनाएं। यह आवेगपूर्ण खरीदारी 40% कम करता है!"
            }
        }
        
        tip_data = tips.get(top_category, tips['food'])
        
        notif = {
            'userId': context.user_id,
            'category': 'tip',
            'notificationType': 'daily',
            'priority': 'low',
            'title': "💡 Money Saving Tip",
            'message': tip_data['en'],
            'titleHindi': "💡 पैसे बचाने का टिप",
            'messageHindi': tip_data['hi'],
            'icon': '💡',
            'color': 'yellow',
            'scheduledFor': self._get_next_scheduled_time(12, 0),
            'bestTimeToShow': dt_time(12, 0),
            'expiresAt': self._get_next_scheduled_time(15, 0),
            'context': {
                'tip_category': top_category,
                'spending_amount': top_amount
            }
        }
        
        self.notifications.append(notif)
    
    async def _generate_milestone_notifications(self, context: NotificationContext):
        """Generate milestone celebration notifications"""
        
        total_savings = context.get_number('totalSavingsLast30Days')
        
        # Savings milestone
        milestones = [1000, 2000, 5000, 10000, 20000, 50000]
        
        for milestone in milestones:
            if abs(total_savings - milestone) < 500:  # Within ₹500 of milestone
                notif = {
                    'userId': context.user_id,
                    'category': 'milestone',
                    'notificationType': 'event_based',
                    'priority': 'normal',
                    'title': f"🎯 Almost There!",
                    'message': f"You're ₹{abs(milestone - total_savings):.0f} away from saving ₹{milestone}!",
                    'titleHindi': f"🎯 लगभग पहुंच गए!",
                    'messageHindi': f"₹{milestone} बचत से सिर्फ ₹{abs(milestone - total_savings):.0f} दूर!",
                    'icon': '🎯',
                    'color': 'green',
                    'scheduledFor': self._get_next_scheduled_time(20, 0),
                    'context': {
                        'milestone': milestone,
                        'current_savings': total_savings,
                        'remaining': abs(milestone - total_savings)
                    }
                }
                
                self.notifications.append(notif)
                break  # Only one milestone notification
    
    def _get_random_morning_message(self, context: NotificationContext) -> str:
        """Get random personalized morning message"""
        
        messages = [
            "Start your day right! Remember to track your expenses today.",
            f"Good to see you, {context.user_name}! Let's make today count!",
            "New day, new opportunities to save! You've got this! 💪",
            "Track your spending today and watch your savings grow! 🌱",
            f"Ready for a great day, {context.user_name}? Let's stay on budget!"
        ]
        
        # Personalize based on risk level
        risk_level = context.insights.get('overallRiskLevel', 'medium')
        
        if risk_level == 'high' or risk_level == 'critical':
            messages.append("Today's focus: Control spending and plan ahead!")
        elif risk_level == 'low':
            messages.append("You're doing great! Keep up the excellent work!")
        
        return random.choice(messages)
    
    def _get_random_morning_message_hindi(self, context: NotificationContext) -> str:
        """Get random personalized morning message in Hindi"""
        
        messages = [
            "अपना दिन अच्छे से शुरू करें! आज अपने खर्चों पर नज़र रखें।",
            f"आपको देखकर अच्छा लगा, {context.user_name}! आज का दिन बेहतरीन बनाएं!",
            "नया दिन, बचत के नए अवसर! आप कर सकते हैं! 💪",
            "आज खर्च ट्रैक करें और अपनी बचत बढ़ते देखें! 🌱",
        ]
        
        return random.choice(messages)
    
    def _get_next_scheduled_time(self, hour: int, minute: int) -> datetime:
        """Get next occurrence of specified time"""
        now = datetime.now()
        scheduled = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        
        if scheduled < now:
            scheduled += timedelta(days=1)
        
        return scheduled
    
    def _get_next_weekday(self, weekday: int) -> datetime:
        """Get next occurrence of specified weekday (0=Monday, 6=Sunday)"""
        now = datetime.now()
        days_ahead = weekday - now.weekday()
        
        if days_ahead <= 0:
            days_ahead += 7
        
        return now + timedelta(days=days_ahead)


class NotificationScheduler:
    """Schedules and saves notifications to database"""
    
    def __init__(self, conn: asyncpg.Connection):
        self.conn = conn
    
    async def schedule_notifications(self, notifications: List[Dict]):
        """Save notifications to database"""
        
        print(f"\n💾 Scheduling {len(notifications)} notifications.")
        
        saved_count = 0
        
        for notif in notifications:
            try:
                # Check if similar notification already exists (avoid duplicates)
                exists = await self._check_duplicate(notif)
                if exists:
                    continue

                # ✅ generate id for this notification
                notif_id = str(uuid.uuid4())

                ctx = notif.get('context')
                ctx = clean_context(ctx) if ctx else None

                await self.conn.execute("""
                    INSERT INTO "UserNotification" (
                        "id",
                        "userId", "category", "notificationType", "priority",
                        "title", "message", "titleHindi", "messageHindi",
                        "icon", "color",
                        "scheduledFor", "bestTimeToShow", "expiresAt",
                        "validFrom", "validUntil",
                        "context", "isInteractive", "actionButton", "actionUrl",
                        "channels"
                    ) VALUES (
                        $1,
                        $2, $3, $4, $5, $6, $7, $8, $9, $10,
                        $11, $12, $13, $14, $15, $16,
                        $17, $18, $19, $20, $21
                    )
                """,
                    notif_id,  # $1
                    notif['userId'],                # $2
                    notif['category'],              # $3
                    notif['notificationType'],      # $4
                    notif['priority'],              # $5
                    notif['title'],                 # $6
                    notif['message'],               # $7
                    notif.get('titleHindi'),        # $8
                    notif.get('messageHindi'),      # $9
                    notif.get('icon'),              # $10
                    notif.get('color'),             # $11
                    notif['scheduledFor'],          # $12
                    notif.get('bestTimeToShow'),    # $13
                    notif.get('expiresAt'),         # $14
                    notif.get('validFrom', datetime.now()),  # $15
                    notif.get('validUntil'),        # $16
                    json.dumps(ctx),                # $17
                    notif.get('isInteractive', False),  # $18
                    notif.get('actionButton'),      # $19
                    notif.get('actionUrl'),         # $20
                    ['in_app', 'push']              # $21
                )
                
                saved_count += 1

            except Exception as e:
                print(f"  ❌ Error saving notification: {e}")
        
        print(f"  ✅ Scheduled {saved_count} notifications")

    async def _check_duplicate(self, notif: Dict) -> bool:
        """Check if similar notification already exists"""
        
        # Check for same category + scheduled time within 1 hour
        exists = await self.conn.fetchval("""
            SELECT EXISTS(
                SELECT 1 FROM "UserNotification"
                WHERE "userId" = $1
                    AND "category" = $2
                    AND "status" IN ('scheduled', 'sent')
                    AND ABS(EXTRACT(EPOCH FROM ("scheduledFor" - $3))) < 3600
            )
        """,
            notif['userId'],
            notif['category'],
            notif['scheduledFor']
        )
        
        return exists


class NotificationOrchestrator:
    """Main orchestrator for notification system"""
    
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
    
    async def generate_for_user(self, user_id: str):
        """Generate notifications for one user"""
        
        print(f"\n{'='*60}")
        print(f"📢 NOTIFICATION GENERATOR - User: {user_id}")
        print(f"{'='*60}")
        
        try:
            # Generate notifications
            generator = NotificationGenerator(self.conn)
            notifications = await generator.generate_for_user(user_id)
            
            if not notifications:
                print("  ℹ️ No new notifications to generate")
                return
            
            # Schedule notifications
            scheduler = NotificationScheduler(self.conn)
            await scheduler.schedule_notifications(notifications)
            
            # Print summary
            self._print_summary(notifications)
            
            return {
                'status': 'success',
                'count': len(notifications)
            }
            
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
            return {'status': 'error', 'message': str(e)}
    
    async def generate_for_all_users(self):
        """Generate notifications for all users"""
        
        user_ids = await self.conn.fetch('SELECT "id" FROM "Customer"')
        
        print(f"\n📢 Generating notifications for {len(user_ids)} users...\n")
        
        total_notifications = 0
        
        for row in user_ids:
            result = await self.generate_for_user(row['id'])
            if result and result['status'] == 'success':
                total_notifications += result.get('count', 0)
        
        print(f"\n{'='*60}")
        print(f"✅ Total Notifications Scheduled: {total_notifications}")
        print(f"{'='*60}")
    
    async def send_due_notifications(self):
        """Send notifications that are due now"""
        
        print("\n📤 Sending due notifications...")
        
        # Get notifications ready to send
        due_notifications = await self.conn.fetch("""
            SELECT * FROM "v_NotificationsReadyToSend"
            LIMIT 100
        """)
        
        if not due_notifications:
            print("  ℹ️ No notifications due right now")
            return
        
        print(f"  📨 Found {len(due_notifications)} notifications to send")
        
        sent_count = 0
        
        for notif in due_notifications:
            try:
                # Mark as sent (in production, actually send via push/SMS/email)
                await self.conn.execute("""
                    UPDATE "UserNotification"
                    SET "status" = 'sent',
                        "sentAt" = CURRENT_TIMESTAMP,
                        "deliveredChannels" = $1
                    WHERE "id" = $2
                """, ['in_app'], notif['id'])
                
                sent_count += 1
                # Log delivery
                print(f"  ✉️ Sent: {notif['title']} → {notif['userName']}")
                
            except Exception as e:
                print(f"  ❌ Failed to send: {e}")
        
        print(f"\n  ✅ Sent {sent_count}/{len(due_notifications)} notifications")

    def _print_summary(self, notifications: List[Dict]):
        """Print summary of generated notifications"""
        
        # Group by category
        by_category = {}
        by_priority = {}
        
        for notif in notifications:
            cat = notif['category']
            pri = notif['priority']
            
            by_category[cat] = by_category.get(cat, 0) + 1
            by_priority[pri] = by_priority.get(pri, 0) + 1
        
        print(f"\n📊 Notification Summary:")
        print(f"\n  By Category:")
        for cat, count in sorted(by_category.items()):
            print(f"    {cat:15s}: {count}")
        
        print(f"\n  By Priority:")
        for pri, count in sorted(by_priority.items()):
            emoji = {'urgent': '🔴', 'high': '🟠', 'normal': '🟡', 'low': '🟢'}.get(pri, '⚪')
            print(f"    {emoji} {pri:10s}: {count}")

async def main():
    """Main entry point"""
    
    import argparse
    
    parser = argparse.ArgumentParser(description="NuoFunds Notification System")
    parser.add_argument('--user-id', type=str, help='Generate for specific user')
    parser.add_argument('--all', action='store_true', help='Generate for all users')
    parser.add_argument('--send', action='store_true', help='Send due notifications')
    
    args = parser.parse_args()
    
    orchestrator = NotificationOrchestrator()
    
    try:
        await orchestrator.connect()
        
        if args.send:
            await orchestrator.send_due_notifications()
        elif args.user_id:
            await orchestrator.generate_for_user(args.user_id)
        elif args.all:
            await orchestrator.generate_for_all_users()
        else:
            # Default: generate for all
            await orchestrator.generate_for_all_users()
    
    finally:
        await orchestrator.close()


if __name__ == "__main__":
    asyncio.run(main())
