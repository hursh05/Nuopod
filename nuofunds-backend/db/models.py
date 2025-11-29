import enum
import uuid
from datetime import datetime

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.dialects.postgresql import UUID, ARRAY, JSONB
from sqlalchemy import Numeric, Index, UniqueConstraint, func

db = SQLAlchemy()


# =========================
# enums
# =========================

class ConsentStatus(enum.Enum):
    PENDING = "PENDING"
    ACTIVE = "ACTIVE"
    REVOKED = "REVOKED"
    EXPIRED = "EXPIRED"


class ConsentFetchType(enum.Enum):
    PERIODIC = "PERIODIC"
    ONETIME = "ONETIME"


class ConsentMode(enum.Enum):
    VIEW = "VIEW"
    STORE = "STORE"
    QUERY = "QUERY"
    STREAM = "STREAM"


class ConsentType(enum.Enum):
    PROFILE = "PROFILE"
    SUMMARY = "SUMMARY"
    TRANSACTIONS = "TRANSACTIONS"


class FinancialInformationType(enum.Enum):
    DEPOSIT = "DEPOSIT"
    TERM_DEPOSIT = "TERM_DEPOSIT"
    RECURRING_DEPOSIT = "RECURRING_DEPOSIT"
    SIP = "SIP"
    CP = "CP"
    GOVT_SECURITIES = "GOVT_SECURITIES"
    EQUITIES = "EQUITIES"
    BONDS = "BONDS"
    DEBENTURES = "DEBENTURES"
    MUTUAL_FUNDS = "MUTUAL_FUNDS"
    ETF = "ETF"
    IDR = "IDR"
    CIS = "CIS"
    AIF = "AIF"
    INSURANCE_POLICIES = "INSURANCE_POLICIES"
    NPS = "NPS"
    INVIT = "INVIT"
    REIT = "REIT"
    GSTR1_3B = "GSTR1_3B"
    OTHER = "OTHER"


class SessionStatus(enum.Enum):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    EXPIRED = "EXPIRED"


class FinancialAccountType(enum.Enum):
    SAVINGS = "SAVINGS"
    CURRENT = "CURRENT"
    CREDIT_CARD = "CREDIT_CARD"
    LOAN = "LOAN"
    WALLET = "WALLET"
    INVESTMENT = "INVESTMENT"
    OTHER = "OTHER"


class TransactionType(enum.Enum):
    CREDIT = "CREDIT"
    DEBIT = "DEBIT"


class WebhookEventType(enum.Enum):
    FI_DATA_READY = "FI_DATA_READY"
    FI_DATA_FAILED = "FI_DATA_FAILED"
    CONSENT_STATUS_UPDATE = "CONSENT_STATUS_UPDATE"
    SESSION_STATUS_UPDATE = "SESSION_STATUS_UPDATE"


# =========================
# models
# =========================

class SetuAccessToken(db.Model):
    __tablename__ = "SetuAccessToken"

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    access_token = db.Column(db.String, nullable=False)
    refresh_token = db.Column(db.String, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)


class Customer(db.Model):
    __tablename__ = "Customer"

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = db.Column(db.String)
    email = db.Column(db.String, unique=True, nullable=False)
    password = db.Column(db.String, nullable=False)
    consent = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    phone = db.Column(db.String, unique=True, nullable=False)

    consents = db.relationship("AccountAggregatorConsent", back_populates="user")
    action_cards = db.relationship("ActionCard", back_populates="customer")
    category_budgets = db.relationship("CategoryBudget", back_populates="customer")
    daily_features = db.relationship("DailyFeatures", back_populates="customer")
    device_tokens = db.relationship("DeviceTokens", back_populates="customer")
    expense_forecasts = db.relationship("ExpenseForecast", back_populates="customer")
    fi_accounts = db.relationship("FinancialAccount", back_populates="user")
    income_forecasts = db.relationship("IncomeForecast", back_populates="customer")
    micro_goals = db.relationship("MicroGoal", back_populates="customer")
    motivation_streaks = db.relationship("MotivationStreak", back_populates="customer")
    notification_analytics = db.relationship("NotificationAnalytics", back_populates="customer")
    notification_preference = db.relationship(
        "NotificationPreference", back_populates="customer", uselist=False
    )
    pipeline_logs = db.relationship("PipelineLog", back_populates="customer")
    shortfalls = db.relationship("Shortfall", back_populates="customer")
    spending_alerts = db.relationship("SpendingAlert", back_populates="customer")
    transactions = db.relationship("Transaction", back_populates="user")
    transaction_classifications = db.relationship(
        "TransactionClassification", back_populates="customer"
    )
    user_financial_insights = db.relationship(
        "UserFinancialInsights", back_populates="customer"
    )
    user_notifications = db.relationship("UserNotification", back_populates="customer")


class AccountAggregatorConsent(db.Model):
    __tablename__ = "AccountAggregatorConsent"
    __table_args__ = (
        Index("ix_AccountAggregatorConsent_userId_consentId", "user_id", "consent_id"),
    )

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey("Customer.id"), nullable=False)
    consent_id = db.Column(db.String, nullable=False)
    pan = db.Column(db.String, nullable=False)
    url = db.Column(db.String, nullable=False)
    tags = db.Column(ARRAY(db.String), nullable=False)
    usage_count = db.Column(db.Integer, nullable=False, default=0)
    last_used = db.Column(db.DateTime)
    vua = db.Column(db.String, nullable=False)
    fi_types = db.Column(ARRAY(db.Enum(FinancialInformationType)), nullable=False)
    purpose_code = db.Column(db.String, nullable=False)
    data_life_unit = db.Column(db.String)
    data_life_value = db.Column(db.Integer)
    frequency_unit = db.Column(db.String)
    frequency_value = db.Column(db.Integer)
    data_range_to_date = db.Column(db.DateTime)
    data_range_from_date = db.Column(db.DateTime)
    fetch_type = db.Column(db.Enum(ConsentFetchType), nullable=False)
    consent_mode = db.Column(db.Enum(ConsentMode), nullable=False)
    consent_types = db.Column(ARRAY(db.Enum(ConsentType)), nullable=False)
    consent_start = db.Column(db.DateTime)
    consent_expiry = db.Column(db.DateTime)
    status = db.Column(db.Enum(ConsentStatus), nullable=False, default=ConsentStatus.PENDING)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = db.relationship("Customer", back_populates="consents")
    accounts = db.relationship("ConsentAccountMapping", back_populates="consent")


class FinancialAccount(db.Model):
    __tablename__ = "FinancialAccount"
    __table_args__ = (
        Index("ix_FinancialAccount_userId_linkRefNumber", "user_id", "link_ref_number"),
    )

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey("Customer.id"), nullable=False)
    fip_id = db.Column(db.String, nullable=False)
    fip_type = db.Column(db.Enum(FinancialInformationType), nullable=False)
    account_type = db.Column(db.String, nullable=False)
    link_ref_number = db.Column(db.String, nullable=False)
    masked_acc_number = db.Column(db.String, nullable=False)

    user = db.relationship("Customer", back_populates="fi_accounts")
    consents = db.relationship("ConsentAccountMapping", back_populates="account")
    financial_account_holders = db.relationship(
        "FinancialAccountHolder", back_populates="financial_account"
    )
    financial_account_summary = db.relationship(
        "FinancialAccountSummary", back_populates="financial_account", uselist=False
    )


class FinancialAccountHolder(db.Model):
    __tablename__ = "FinancialAccountHolder"

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = db.Column(db.String, nullable=False)
    dob = db.Column(db.String, nullable=False)
    pan = db.Column(db.String, nullable=False)
    email = db.Column(db.String, nullable=False)
    mobile = db.Column(db.String, nullable=False)
    address = db.Column(db.String, nullable=False)
    nominee = db.Column(db.String, nullable=False)
    ckyc_compliance = db.Column(db.String, nullable=False)
    financial_account_id = db.Column(
        UUID(as_uuid=True), db.ForeignKey("FinancialAccount.id"), nullable=False
    )

    financial_account = db.relationship("FinancialAccount", back_populates="financial_account_holders")


class ConsentAccountMapping(db.Model):
    __tablename__ = "ConsentAccountMapping"
    __table_args__ = (
        Index("ix_ConsentAccountMapping_accountId", "account_id"),
    )

    consent_id = db.Column(
        UUID(as_uuid=True),
        db.ForeignKey("AccountAggregatorConsent.id"),
        primary_key=True,
    )
    account_id = db.Column(
        UUID(as_uuid=True),
        db.ForeignKey("FinancialAccount.id"),
        primary_key=True,
    )
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    account = db.relationship("FinancialAccount", back_populates="consents")
    consent = db.relationship("AccountAggregatorConsent", back_populates="accounts")


class Transaction(db.Model):
    __tablename__ = "Transaction"
    __table_args__ = (
        Index("ix_Transaction_userId", "userId"),
        Index("ix_Transaction_financialAccountId", "financial_account_id"),
    )

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = db.Column(
        "userId",                          # <-- FIXED HERE
        UUID(as_uuid=True),
        db.ForeignKey("Customer.id"),
        nullable=False
    )
    mode = db.Column(db.String, nullable=False)
    type = db.Column(db.String, nullable=False)
    txn_id = db.Column("txnId", db.String)
    amount = db.Column(Numeric(10, 2), nullable=False)
    balance = db.Column(Numeric(10, 2))
    narration = db.Column(db.String)
    reference = db.Column(db.String)
    comment = db.Column(db.String)
    date = db.Column(db.DateTime, nullable=False)
    value_data = db.Column(db.DateTime)
    fi_type = db.Column(db.Enum(FinancialInformationType))
    financial_account_id = db.Column(UUID(as_uuid=True), db.ForeignKey("FinancialAccount.id"))

    user = db.relationship("Customer", back_populates="transactions")
    spending_alerts = db.relationship("SpendingAlert", back_populates="transaction")
    transaction_classification = db.relationship(
        "TransactionClassification", back_populates="transaction", uselist=False
    )


class FinancialAccountSummary(db.Model):
    __tablename__ = "FinancialAccountSummary"

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    financial_account_id = db.Column(
        UUID(as_uuid=True), db.ForeignKey("FinancialAccount.id"), unique=True, nullable=False
    )
    branch = db.Column(db.String)
    ifsc = db.Column(db.String)
    micr_code = db.Column(db.String)
    opening_date = db.Column(db.DateTime)
    current_value = db.Column(db.String)
    status = db.Column(db.String)
    account_sub_type = db.Column(db.String)
    pending_amount = db.Column(db.String)
    pending_txn_type = db.Column(db.String)
    currency = db.Column(db.String)
    facility = db.Column(db.String)
    drawing_limit = db.Column(db.String)
    current_balance = db.Column(db.String)
    current_od_limit = db.Column(db.String)
    balance_date_time = db.Column(db.DateTime)
    tenure_days = db.Column(db.String)
    tenure_months = db.Column(db.String)
    tenure_years = db.Column(db.String)
    interest_rate = db.Column(db.String)
    maturity_date = db.Column(db.DateTime)
    maturity_amount = db.Column(db.String)
    principal_amount = db.Column(db.String)
    interest_payout = db.Column(db.String)
    interest_computation = db.Column(db.String)
    compounding_frequency = db.Column(db.String)
    recurring_amount = db.Column(db.String)
    recurring_deposit_day = db.Column(db.String)
    interest_on_maturity = db.Column(db.String)
    interest_periodic_payout_amount = db.Column(db.String)
    description = db.Column(db.String)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    financial_account = db.relationship("FinancialAccount", back_populates="financial_account_summary")


class SetuWebhook(db.Model):
    __tablename__ = "SetuWebhook"
    __table_args__ = (
        Index("ix_SetuWebhook_eventType", "event_type"),
    )

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    event_type = db.Column(db.Enum(WebhookEventType), nullable=False)
    payload = db.Column(JSONB)
    error = db.Column(JSONB)
    success = db.Column(db.Boolean, nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False)
    consent_id = db.Column(db.String)


class DailyFeatures(db.Model):
    __tablename__ = "DailyFeatures"
    __table_args__ = (
        UniqueConstraint("user_id", "date", name="uq_DailyFeatures_userId_date"),
        Index("ix_DailyFeatures_userId_date_desc", "user_id", "date"),
    )

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey("Customer.id"), nullable=False)
    date = db.Column(db.Date, nullable=False)
    total_income = db.Column(Numeric(12, 2), default=0)
    total_expense = db.Column(Numeric(12, 2), default=0)
    net_amount = db.Column(Numeric(12, 2))
    transaction_count = db.Column(db.Integer, default=0)
    closing_balance = db.Column(Numeric(12, 2))
    rolling7_mean = db.Column(Numeric(12, 2))
    rolling30_mean = db.Column(Numeric(12, 2))
    rolling7_std = db.Column(Numeric(12, 2))
    day_of_week = db.Column(db.Integer)
    is_weekend = db.Column(db.Boolean)
    month = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    customer = db.relationship("Customer", back_populates="daily_features")


class ExpenseForecast(db.Model):
    __tablename__ = "ExpenseForecast"
    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "forecast_date",
            "category",
            "generated_at",
            name="ExpenseForecast_userId_forecastDate_category_key",
        ),
        Index(
            "ExpenseForecast_userId_category_idx",
            "user_id",
            "category",
            "forecast_date",
        ),
    )

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey("Customer.id"), nullable=False)
    forecast_date = db.Column(db.Date, nullable=False)
    category = db.Column(db.String, nullable=False)
    predicted_expense = db.Column(Numeric(12, 2), nullable=False)
    confidence = db.Column(Numeric(5, 4))
    model_used = db.Column(db.String)
    generated_at = db.Column(db.DateTime, default=datetime.utcnow)

    customer = db.relationship("Customer", back_populates="expense_forecasts")


class IncomeForecast(db.Model):
    __tablename__ = "IncomeForecast"
    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "forecast_date",
            "generated_at",
            name="IncomeForecast_userId_forecastDate_key",
        ),
        Index("ix_IncomeForecast_userId_forecastDate_desc", "user_id", "forecast_date"),
    )

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey("Customer.id"), nullable=False)
    forecast_date = db.Column(db.Date, nullable=False)
    predicted_income = db.Column(Numeric(12, 2), nullable=False)
    confidence = db.Column(Numeric(5, 4))
    model_used = db.Column(db.String)
    mape = db.Column(Numeric(8, 4))
    generated_at = db.Column(db.DateTime, default=datetime.utcnow)

    customer = db.relationship("Customer", back_populates="income_forecasts")


class PipelineLog(db.Model):
    __tablename__ = "PipelineLog"
    __table_args__ = (
        Index("PipelineLog_userId_idx", "user_id", "started_at"),
    )

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey("Customer.id"))
    stage = db.Column(db.String, nullable=False)
    status = db.Column(db.String, nullable=False)
    message = db.Column(db.String)
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)
    duration = db.Column(db.Integer)

    customer = db.relationship("Customer", back_populates="pipeline_logs")


class TransactionClassification(db.Model):
    __tablename__ = "TransactionClassification"
    __table_args__ = (
        Index("ix_TransactionClassification_category", "category"),
        Index("ix_TransactionClassification_isIncome", "isIncome"),
        Index("ix_TransactionClassification_userId", "user_id"),
    )

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    transaction_id = db.Column(
        "transactionId",                 # <-- FIXED HERE
        UUID(as_uuid=True),
        db.ForeignKey("Transaction.id"),
        unique=True,
        nullable=False
    )
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey("Customer.id"), nullable=False)
    is_income = db.Column(
        "isIncome",      # <-- FIXED
        db.Boolean,
        default=False,
        nullable=False
    )
    category = db.Column(db.String, nullable=False)
    merchant_name = db.Column(db.String)
    confidence = db.Column(Numeric(5, 4))
    narration_normalized = db.Column(db.String)
    classified_at = db.Column(db.DateTime, default=datetime.utcnow)

    transaction = db.relationship("Transaction", back_populates="transaction_classification")
    customer = db.relationship("Customer", back_populates="transaction_classifications")


class ActionCard(db.Model):
    __tablename__ = "ActionCard"
    __table_args__ = (
        Index("ActionCard_priority_idx", "priority", "status"),
        Index("ActionCard_userId_status_idx", "user_id", "status", "priority"),
        Index("ix_ActionCard_userId_validFrom_desc", "user_id", "valid_from"),
    )

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey("Customer.id"), nullable=False)
    insight_id = db.Column(UUID(as_uuid=True), db.ForeignKey("UserFinancialInsights.id"))
    card_type = db.Column(db.String, nullable=False)
    priority = db.Column(db.String, nullable=False)
    category = db.Column(db.String)
    title = db.Column(db.String, nullable=False)
    message = db.Column(db.String, nullable=False)
    message_hindi = db.Column(db.String)
    icon = db.Column(db.String)
    color = db.Column(db.String)
    action_type = db.Column(db.String)
    action_amount = db.Column(Numeric(12, 2))
    action_category = db.Column(db.String)
    action_description = db.Column(db.String)
    expected_savings = db.Column(Numeric(12, 2))
    expected_impact_days = db.Column(db.Integer)
    impact_description = db.Column(db.String)
    valid_from = db.Column(db.DateTime, default=datetime.utcnow)
    valid_until = db.Column(db.DateTime)
    show_after = db.Column(db.DateTime)
    is_urgent = db.Column(db.Boolean, default=False)
    days_until_impact = db.Column(db.Integer)
    status = db.Column(db.String, default="pending")
    shown_at = db.Column(db.DateTime)
    responded_at = db.Column(db.DateTime)
    completed_at = db.Column(db.DateTime)
    user_response = db.Column(JSONB)
    completion_proof = db.Column(JSONB)
    acceptance_likelihood = db.Column(Numeric(5, 4))
    acceptance_factors = db.Column(ARRAY(db.String))
    rejection_reasons = db.Column(ARRAY(db.String))
    related_forecast_id = db.Column(db.String)
    related_transaction_ids = db.Column(ARRAY(db.String))
    trigger_event = db.Column(db.String)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user_financial_insights = db.relationship(
        "UserFinancialInsights", back_populates="action_cards"
    )
    customer = db.relationship("Customer", back_populates="action_cards")
    user_notifications = db.relationship("UserNotification", back_populates="action_card")


class CategoryBudget(db.Model):
    __tablename__ = "CategoryBudget"
    __table_args__ = (
        UniqueConstraint("user_id", "category", "month", name="uq_CategoryBudget_user_category_month"),
        Index("ix_CategoryBudget_userId_month", "user_id", "month"),
    )

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey("Customer.id"), nullable=False)
    category = db.Column(db.String, nullable=False)
    monthly_budget = db.Column(Numeric(12, 2), nullable=False)
    daily_budget = db.Column(Numeric(12, 2))
    current_month_spend = db.Column(Numeric(12, 2), default=0)
    remaining_budget = db.Column(Numeric(12, 2))
    percent_used = db.Column(Numeric(12, 2))
    days_remaining_in_month = db.Column(db.Integer)
    is_exceeded = db.Column(db.Boolean, default=False)
    exceeded_by = db.Column(Numeric(12, 2))
    status = db.Column(db.String, default="active")
    alert_threshold = db.Column(Numeric(12, 2), default=80)
    alert_sent = db.Column(db.Boolean, default=False)
    month = db.Column(db.Date)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    customer = db.relationship("Customer", back_populates="category_budgets")


class MicroGoal(db.Model):
    __tablename__ = "MicroGoal"
    __table_args__ = (
        Index("ix_MicroGoal_userId_status", "user_id", "status"),
    )

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey("Customer.id"), nullable=False)
    goal_name = db.Column(db.String, nullable=False)
    goal_type = db.Column(db.String, nullable=False)
    target_amount = db.Column(Numeric(12, 2), nullable=False)
    current_amount = db.Column(Numeric(12, 2), default=0)
    daily_target = db.Column(Numeric(12, 2))
    start_date = db.Column(db.Date, server_default=func.current_date())
    target_date = db.Column(db.Date)
    days_remaining = db.Column(db.Integer)
    progress_percent = db.Column(Numeric(12, 2))
    on_track = db.Column(db.Boolean, default=True)
    days_ahead = db.Column(db.Integer)
    status = db.Column(db.String, default="active")
    priority = db.Column(db.String, default="medium")
    motivation_message = db.Column(db.String)
    milestone_messages = db.Column(ARRAY(db.String))
    last_encouragement_date = db.Column(db.Date)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = db.Column(db.DateTime)

    customer = db.relationship("Customer", back_populates="micro_goals")


class MotivationStreak(db.Model):
    __tablename__ = "MotivationStreak"
    __table_args__ = (
        UniqueConstraint("user_id", "streak_type", name="uq_MotivationStreak_userId_streakType"),
        Index("ix_MotivationStreak_userId", "user_id"),
    )

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey("Customer.id"), nullable=False)
    streak_type = db.Column(db.String, nullable=False)
    current_streak = db.Column(db.Integer, default=0)
    longest_streak = db.Column(db.Integer, default=0)
    total_count = db.Column(db.Integer, default=0)
    last_activity_date = db.Column(db.Date)
    streak_start_date = db.Column(db.Date)
    milestones_achieved = db.Column(ARRAY(db.Integer), default=[])
    next_milestone = db.Column(db.Integer)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    customer = db.relationship("Customer", back_populates="motivation_streaks")


class NotificationAnalytics(db.Model):
    __tablename__ = "NotificationAnalytics"
    __table_args__ = (
        Index("ix_NotificationAnalytics_notificationId", "notification_id"),
    )

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    notification_id = db.Column(
        UUID(as_uuid=True), db.ForeignKey("UserNotification.id"), nullable=False
    )
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey("Customer.id"), nullable=False)
    delivery_attempts = db.Column(db.Integer, default=0)
    successful_deliveries = db.Column(db.Integer, default=0)
    failed_deliveries = db.Column(db.Integer, default=0)
    delivery_latency = db.Column(db.Integer)
    time_to_first_view = db.Column(db.Integer)
    time_to_action = db.Column(db.Integer)
    view_duration = db.Column(db.Integer)
    was_clicked = db.Column(db.Boolean, default=False)
    was_dismissed = db.Column(db.Boolean, default=False)
    was_acted_upon = db.Column(db.Boolean, default=False)
    sentiment = db.Column(db.String)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user_notification = db.relationship(
        "UserNotification", back_populates="notification_analytics"
    )
    customer = db.relationship("Customer", back_populates="notification_analytics")


class NotificationPreference(db.Model):
    __tablename__ = "NotificationPreference"

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = db.Column(
        UUID(as_uuid=True), db.ForeignKey("Customer.id"), unique=True, nullable=False
    )
    notifications_enabled = db.Column(db.Boolean, default=True)
    preferred_language = db.Column(db.String, default="en")
    in_app_enabled = db.Column(db.Boolean, default=True)
    push_enabled = db.Column(db.Boolean, default=True)
    email_enabled = db.Column(db.Boolean, default=False)
    sms_enabled = db.Column(db.Boolean, default=False)
    whatsapp_enabled = db.Column(db.Boolean, default=False)
    motivation_enabled = db.Column(db.Boolean, default=True)
    reminder_enabled = db.Column(db.Boolean, default=True)
    milestone_enabled = db.Column(db.Boolean, default=True)
    tip_enabled = db.Column(db.Boolean, default=True)
    warning_enabled = db.Column(db.Boolean, default=True)
    celebration_enabled = db.Column(db.Boolean, default=True)
    quiet_hours_start = db.Column(db.Time)
    quiet_hours_end = db.Column(db.Time)
    preferred_morning_time = db.Column(db.Time, server_default=func.time("09:00:00"))
    preferred_evening_time = db.Column(db.Time, server_default=func.time("18:00:00"))
    max_daily_notifications = db.Column(db.Integer, default=3)
    max_weekly_notifications = db.Column(db.Integer, default=10)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    customer = db.relationship("Customer", back_populates="notification_preference")


class NotificationTemplate(db.Model):
    __tablename__ = "NotificationTemplate"
    __table_args__ = (
        Index("ix_NotificationTemplate_category", "category"),
        Index("ix_NotificationTemplate_triggerType", "trigger_type"),
    )

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    template_key = db.Column(db.String, unique=True, nullable=False)
    category = db.Column(db.String, nullable=False)
    trigger_type = db.Column(db.String, nullable=False)
    title_english = db.Column(db.String, nullable=False)
    message_english = db.Column(db.String, nullable=False)
    title_hindi = db.Column(db.String)
    message_hindi = db.Column(db.String)
    variables = db.Column(ARRAY(db.String), nullable=False)
    icon = db.Column(db.String)
    color = db.Column(db.String)
    condition_type = db.Column(db.String)
    condition_operator = db.Column(db.String)
    condition_value = db.Column(Numeric(12, 2))
    additional_conditions = db.Column(JSONB)
    preferred_time = db.Column(db.Time)
    frequency = db.Column(db.String)
    cooldown_days = db.Column(db.Integer, default=0)
    priority = db.Column(db.String, default="normal")
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user_notifications = db.relationship("UserNotification", back_populates="notification_template")


class Shortfall(db.Model):
    __tablename__ = "Shortfall"
    __table_args__ = (
        Index("ix_Shortfall_userId_forecastDate_desc", "user_id", "forecast_date"),
    )

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey("Customer.id"), nullable=False)
    forecast_date = db.Column(db.Date, nullable=False)
    predicted_income = db.Column(Numeric(12, 2), nullable=False)
    predicted_expense = db.Column(Numeric(12, 2), nullable=False)
    predicted_shortfall = db.Column(Numeric(12, 2), nullable=False)
    is_deficit = db.Column(db.Boolean, nullable=False)
    risk_level = db.Column(db.String, nullable=False)
    generated_at = db.Column(db.DateTime, default=datetime.utcnow)

    customer = db.relationship("Customer", back_populates="shortfalls")


class SpendingAlert(db.Model):
    __tablename__ = "SpendingAlert"
    __table_args__ = (
        Index("ix_SpendingAlert_userId_status", "user_id", "status"),
    )

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey("Customer.id"), nullable=False)
    alert_type = db.Column(db.String, nullable=False)
    severity = db.Column(db.String, nullable=False)
    category = db.Column(db.String)
    title = db.Column(db.String, nullable=False)
    message = db.Column(db.String, nullable=False)
    detected_amount = db.Column(Numeric(12, 2))
    normal_amount = db.Column(Numeric(12, 2))
    percentage_deviation = db.Column(Numeric(12, 2))
    transaction_id = db.Column(UUID(as_uuid=True), db.ForeignKey("Transaction.id"))
    detected_at = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String, default="active")
    acknowledged_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    transaction = db.relationship("Transaction", back_populates="spending_alerts")
    customer = db.relationship("Customer", back_populates="spending_alerts")


class UserFinancialInsights(db.Model):
    __tablename__ = "UserFinancialInsights"
    __table_args__ = (
        UniqueConstraint(
            "user_id", "analysis_date", name="UserFinancialInsights_userId_key"
        ),
        Index("UserFinancialInsights_riskLevel_idx", "overall_risk_level"),
        Index("UserFinancialInsights_userId_idx", "user_id", "analysis_date"),
    )

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey("Customer.id"), nullable=False)
    analysis_date = db.Column(db.DateTime, default=datetime.utcnow)
    analysis_period_days = db.Column(db.Integer, default=30)
    avg_daily_income = db.Column(Numeric(12, 2))
    income_stability = db.Column(db.String)
    income_stability_score = db.Column(Numeric(12, 2))
    income_growth_rate = db.Column(Numeric(12, 2))
    lowest_income_week = db.Column(Numeric(12, 2))
    highest_income_week = db.Column(Numeric(12, 2))
    weekend_income_boost = db.Column(Numeric(12, 2))
    avg_daily_expense = db.Column(Numeric(12, 2))
    expense_stability = db.Column(db.String)
    top_expense_category = db.Column(db.String)
    top_expense_category_amount = db.Column(Numeric(12, 2))
    top_expense_category_percent = db.Column(Numeric(12, 2))
    unnecessary_spending_amount = db.Column(Numeric(12, 2))
    avg_daily_savings = db.Column(Numeric(12, 2))
    savings_rate = db.Column(Numeric(12, 2))
    total_savings_last30_days = db.Column(Numeric(12, 2))
    savings_consistency = db.Column(db.String)
    days_with_zero_savings = db.Column(db.Integer)
    avg_daily_balance = db.Column(Numeric(12, 2))
    lowest_balance = db.Column(Numeric(12, 2))
    lowest_balance_date = db.Column(db.Date)
    days_with_negative_cashflow = db.Column(db.Integer)
    days_with_low_balance = db.Column(db.Integer)
    cash_crunch_risk = db.Column(db.String)
    impulsive_purchases = db.Column(db.Integer)
    spending_pattern_type = db.Column(db.String)
    average_transaction_size = db.Column(Numeric(12, 2))
    high_value_transactions = db.Column(db.Integer)
    overall_risk_level = db.Column(db.String)
    risk_score = db.Column(Numeric(12, 2))
    risk_factors = db.Column(ARRAY(db.String))
    strengths = db.Column(ARRAY(db.String))
    weaknesses = db.Column(ARRAY(db.String))
    recommended_daily_savings = db.Column(Numeric(12, 2))
    recommended_emergency_fund = db.Column(Numeric(12, 2))
    months_to_emergency_fund = db.Column(Numeric(12, 2))
    spending_peak_day = db.Column(db.String)
    spending_peak_time = db.Column(db.String)
    budget_adherence = db.Column(Numeric(12, 2))
    predicted_shortfall_days = db.Column(db.Integer)
    predicted_shortfall_amount = db.Column(Numeric(12, 2))
    next_low_balance_date = db.Column(db.Date)
    financial_health_grade = db.Column(db.String)
    insights_summary = db.Column(db.String)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    action_cards = db.relationship("ActionCard", back_populates="user_financial_insights")
    customer = db.relationship("Customer", back_populates="user_financial_insights")
    user_notifications = db.relationship("UserNotification", back_populates="user_financial_insights")


class UserNotification(db.Model):
    __tablename__ = "UserNotification"
    __table_args__ = (
        Index("ix_UserNotification_status_priority", "status", "priority"),
        Index("ix_UserNotification_userId_category", "user_id", "category"),
        Index("UserNotification_userId_status_idx", "user_id", "status", "scheduled_for"),
    )

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey("Customer.id"), nullable=False)
    template_id = db.Column(UUID(as_uuid=True), db.ForeignKey("NotificationTemplate.id"))
    title = db.Column(db.String, nullable=False)
    message = db.Column(db.String, nullable=False)
    title_hindi = db.Column(db.String)
    message_hindi = db.Column(db.String)
    icon = db.Column(db.String)
    color = db.Column(db.String)
    category = db.Column(db.String, nullable=False)
    notification_type = db.Column(db.String, nullable=False)
    priority = db.Column(db.String, default="normal")
    context = db.Column(JSONB)
    personalized_data = db.Column(JSONB)
    related_insight_id = db.Column(
        UUID(as_uuid=True), db.ForeignKey("UserFinancialInsights.id")
    )
    related_action_card_id = db.Column(
        UUID(as_uuid=True), db.ForeignKey("ActionCard.id")
    )
    scheduled_for = db.Column(db.DateTime, nullable=False)
    best_time_to_show = db.Column(db.Time)
    expires_at = db.Column(db.DateTime)
    valid_from = db.Column(db.DateTime, default=datetime.utcnow)
    valid_until = db.Column(db.DateTime)
    status = db.Column(db.String, default="scheduled")
    sent_at = db.Column(db.DateTime)
    shown_at = db.Column(db.DateTime)
    read_at = db.Column(db.DateTime)
    dismissed_at = db.Column(db.DateTime)
    is_interactive = db.Column(db.Boolean, default=False)
    action_button = db.Column(db.String)
    action_url = db.Column(db.String)
    user_response = db.Column(JSONB)
    impressions = db.Column(db.Integer, default=0)
    clicks = db.Column(db.Integer, default=0)
    engagement_score = db.Column(Numeric(5, 2))
    channels = db.Column(ARRAY(db.String))
    delivered_channels = db.Column(ARRAY(db.String))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    notification_analytics = db.relationship(
        "NotificationAnalytics", back_populates="user_notification"
    )   
    action_card = db.relationship("ActionCard", back_populates="user_notifications")
    user_financial_insights = db.relationship(
        "UserFinancialInsights", back_populates="user_notifications"
    )
    notification_template = db.relationship(
        "NotificationTemplate", back_populates="user_notifications"
    )
    customer = db.relationship("Customer", back_populates="user_notifications")


class DeviceTokens(db.Model):
    __tablename__ = "DeviceTokens"
    __table_args__ = (
        Index("ix_DeviceTokens_userId", "user_id"),
    )

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    token = db.Column(db.String, unique=True, nullable=False)
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey("Customer.id"), nullable=False)
    device_type = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    customer = db.relationship("Customer", back_populates="device_tokens")
