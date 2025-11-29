# NuoFunds - Financial Intelligence Platform

- Video Demo Link: https://youtu.be/j9bJCdkhMw4?si=HOkF_0BoIs5Z33Hn

A complete financial management ecosystem for India's gig workers, helping them track spending, forecast income, and achieve financial goals through intelligent AI-driven insights.

---

## Problem

India's 12+ million gig workers face chronic financial instability:
- 75% experience stress from irregular earnings
- 70% are denied loans due to inconsistent income
- Less than 15% have savings or insurance

These workers earn ₹800-₹1,200 daily but struggle with unpredictable cash flow and lack personalized financial guidance.

---

## Solution

NuoFunds is a three-part platform that turns transactional chaos into financial clarity:

1. *Mobile App* - Track finances on the go
2. *Admin Backend* - Manage users and platform operations
3. *AI Engine* - Generate insights and recommendations

---

## Architecture
[![nuofund-architecture.png](https://i.postimg.cc/d0GDmXDc/nuofund-architecture.png)](https://postimg.cc/4KNJXWzW)

---

## How It Works

### 1. User Registration & Consent

- User registers through the mobile app
- App redirects to Setu Account Aggregator for consent
- User authorizes access to their financial accounts
- Setu sends transaction data to our webhook

### 2. Data Processing

When transaction data arrives:

*Pipeline 1: Transaction Classification*
- Receives raw transaction data from Setu webhook
- Categorizes each transaction (food, travel, rent, utilities, etc.)
- Stores classified data in database

*Pipeline 2: Financial Analysis*
- Analyzes classified transactions
- Generates income forecast
- Generates expense forecast
- Predicts cash shortfall periods based on spending patterns

*Pipeline 3: Daily Intelligence (Agentic AI)*
- *Feature Analyzer Agent*: Extracts daily behavioral patterns
- *Action Card Agent*: Creates personalized recommendations ("Save ₹200 today", "High spending alert")
- *Notification Agent*: Generates timely motivational messages

### 3. Data Display

- Next.js backend fetches processed insights from Python engine
- Formats data for mobile app consumption
- Mobile app displays:
  - Spending breakdown by category (pie charts)
  - Income vs expense trends (line charts)
  - Monthly comparisons (bar charts)
  - Shortfall warnings
  - Action cards

### 4. Goal Management (Upcoming)

- User sets savings goal (e.g., "Save ₹20,000 in 3 months")
- AI engine calculates required daily/weekly savings
- Generates actionable spending adjustments
- Tracks progress and sends reminders

---

## Technology Stack

### Mobile App (nuofunds)
- *Framework*: React Native with Expo
- *Features*: 
  - User authentication
  - Transaction viewing
  - Visual analytics (charts)
  - Goal setting interface

### Admin Backend (nuofunds-admin)
- *Framework*: Next.js
- *Database*: PostgreSQL
- *ORM*: Prisma
- *Responsibilities*:
  - User registration and authentication
  - Setu Account Aggregator integration
  - Webhook handling
  - API endpoints for mobile app
  - Future: Admin dashboard for platform management

### AI Engine (nuofunds-backend)
- *Language*: Python
- *Framework*: Flask
- *AI/ML Libraries*: 
  - Prophet (forecasting)
  - Light GBM
  - Time Series
- *Responsibilities*:
  - Transaction classification
  - Income/expense forecasting
  - Shortfall prediction
  - Agentic AI workflows
  - Action card generation

---

## Data Flow

User Account Registration
         ↓
    Setu AA (Consent)
         ↓
Webhook → Next.js Backend
         ↓
Raw Transaction Data
         ↓
Python AI Engine
    │
    ├→ Classify Transactions
    ├→ Forecast Income/Expenses
    ├→ Predict Shortfalls
    └→ Generate Action Cards
         ↓
Next.js Backend (API)
         ↓
Mobile App (Visualizations)


---

## Key Features

### Current
- *Automated Transaction Import*: Via Setu Account Aggregator
- *Smart Categorization*: AI classifies spending automatically
- *Income Forecasting*: Predicts future earnings based on patterns
- *Expense Forecasting*: Anticipates upcoming spending
- *Shortfall Alerts*: Warns when low balance is likely
- *Visual Analytics*: Charts showing spending by category and trends
- *Action Cards*: Daily personalized recommendations

### Upcoming
- *Goal-Based Savings*: Set targets and get actionable plans
- *Advisor Connect*: Video consultations with financial planners
- *Early Wage Access*: Integration with EWA providers like KarmaLife
- *Micro-Investments*: Small daily savings in SIPs or gold

---

## Target Users

- Delivery partners (Swiggy, Zomato, Dunzo)
- Ride-hailing drivers (Ola, Uber)
- Home service professionals (Urban Company)
- Freelancers
- Small shop owners

## Future Scope

### Platform Enhancements
- Admin dashboard for user management
- Partner onboarding (financial advisors, EWA providers)
- Subscription management system
- Multi-language support (Hindi, Marathi, Tamil, Bengali)

### Intelligence Upgrades
- Conversational chat interface
- Behavioral learning (adapts to user preferences)

---

## Setup Instructions

### Prerequisites
- Node.js 18+
- Python 3.9+
- PostgreSQL
- Expo CLI
- NextJs 15+
