from sqlalchemy import Column, String, DateTime, Numeric, Boolean, JSON, ForeignKey, Integer, LargeBinary, Float, Text
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import relationship
from app.db.session import Base
import uuid
from datetime import datetime


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    first_name = Column(String(100))
    last_name = Column(String(100))
    role = Column(String(50), default="customer")
    is_active = Column(Boolean, default=True)
    subscription_tier = Column(String(50), default="free")
    stripe_customer_id = Column(String(255))
    stripe_subscription_id = Column(String(255))
    refresh_token = Column(String(255))
    phone_number = Column(String(20))  # For SMS alerts (Hunter tier)
    # WebAuthn / passkey fields
    credential_id = Column(String(255))
    public_key = Column(LargeBinary)
    sign_count = Column(Integer, default=0)
    aaguid = Column(String(255))
    # Niche subscriptions — users pick which categories they want alerts for.
    # Empty/None means "all niches".
    subscribed_niches = Column(ARRAY(String), default=list)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    subscriptions = relationship("Subscription", back_populates="user", cascade="all, delete-orphan")
    alerts = relationship("Alert", back_populates="user", cascade="all, delete-orphan")
    watchlist_items = relationship("WatchlistItem", back_populates="user", cascade="all, delete-orphan")

    @property
    def full_name(self) -> str:
        parts = [self.first_name, self.last_name]
        return " ".join(p for p in parts if p) or self.email


class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    stripe_subscription_id = Column(String(255), unique=True)
    status = Column(String(50))
    tier = Column(String(50))
    current_period_end = Column(DateTime)
    cancel_at_period_end = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="subscriptions")


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    type = Column(String(50), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(String)
    source_url = Column(String(500))
    potential_profit = Column(Numeric(10, 2))
    status = Column(String(50), default="pending")
    sent_at = Column(DateTime)
    is_read = Column(Boolean, default=False)
    read_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="alerts")


class PriceSnapshot(Base):
    __tablename__ = "price_snapshots"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    item_id = Column(String(255), nullable=False, index=True)
    retailer = Column(String(100), nullable=False)
    price = Column(Numeric(10, 2), nullable=False)
    currency = Column(String(3), default="USD")
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)


class WatchlistItem(Base):
    __tablename__ = "watchlist_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    item_name = Column(String(255), nullable=False)
    target_price = Column(Numeric(10, 2))
    current_price = Column(Numeric(10, 2))
    retailers = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="watchlist_items")


class WaitlistEntry(Base):
    __tablename__ = "waitlist_entries"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    plan = Column(String(255))
    source = Column(String(255))
    message = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)


class ArbitrageDeal(Base):
    """Detected arbitrage opportunity between buy/sell platforms."""
    __tablename__ = "arbitrage_deals"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    asin = Column(String(100), nullable=False, index=True)
    title = Column(String(500), nullable=False)
    image_url = Column(String(1000))
    buy_url = Column(String(1000))
    buy_platform = Column(String(50), default="amazon")
    retailer = Column(String(100), default="amazon", index=True)  # amazon, home_depot, ace_hardware, corsair, etc.
    deal_source = Column(String(20), default="online")  # online, in_store
    buy_price = Column(Numeric(10, 2), nullable=False)
    sell_platform = Column(String(50), default="ebay")
    sell_price = Column(Numeric(10, 2), nullable=False)
    historical_avg = Column(Numeric(10, 2))
    discrepancy = Column(Numeric(5, 4))  # Percentage as decimal (0.50 = 50%)
    deal_tier = Column(String(20), default="arbitrage")  # glitch, clearance, arbitrage, watch
    net_profit = Column(Numeric(10, 2))
    roi = Column(Numeric(5, 4))  # 0.25 = 25%
    total_costs = Column(Numeric(10, 2))
    platform_fee = Column(Numeric(10, 2))
    bsr = Column(Integer)
    category = Column(String(100))
    niche = Column(String(50), nullable=True, index=True)  # electronics, tools, etc.
    is_profitable = Column(Boolean, default=False)
    status = Column(String(50), default="active")  # active, alerted, expired, rejected
    detected_at = Column(DateTime, default=datetime.utcnow, index=True)
    alerted_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)


class ScanRun(Base):
    """Track scan runs for monitoring and deduplication."""
    __tablename__ = "scan_runs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    scan_type = Column(String(50), default="amazon_ebay")  # amazon_ebay, walmart_ebay, etc.
    products_scanned = Column(Integer, default=0)
    deals_found = Column(Integer, default=0)
    deals_alerted = Column(Integer, default=0)
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)
    status = Column(String(50), default="running")  # running, completed, failed
    error = Column(String)


class CouponCode(Base):
    """Scraped coupon / promo code for a retailer."""
    __tablename__ = "coupon_codes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code = Column(String(100), nullable=False, index=True)
    retailer = Column(String(100), nullable=False, index=True)  # amazon, walmart, target, etc.
    title = Column(String(500), nullable=False)
    description = Column(String)
    discount_type = Column(String(20), default="percentage")  # percentage, fixed, free_shipping
    discount_value = Column(Numeric(10, 2), default=0)  # percentage (e.g. 20 = 20%) or dollar amount
    min_purchase = Column(Numeric(10, 2))  # minimum order amount required
    max_discount = Column(Numeric(10, 2))  # cap on discount for percentage codes
    category = Column(String(100))  # electronics, home, etc. (nullable = any)
    product_url = Column(String(1000))  # specific product URL if applicable
    source = Column(String(100), default="scraped")  # scraped, manual, api
    source_url = Column(String(1000))  # where we scraped it from
    expires_at = Column(DateTime, index=True)
    verified = Column(Boolean, default=False)
    verified_at = Column(DateTime)
    times_used = Column(Integer, default=0)
    success_count = Column(Integer, default=0)
    fail_count = Column(Integer, default=0)
    status = Column(String(20), default="active")  # active, expired, used_up, unverified
    scraped_at = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class NotificationLog(Base):
    """Track deal notifications sent to each channel."""
    __tablename__ = "notification_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    deal_id = Column(UUID(as_uuid=True), ForeignKey("arbitrage_deals.id"), nullable=True)
    asin = Column(String(20), index=True)
    channel = Column(String(50), nullable=False)  # discord, telegram, twitter, facebook, sms, email, dashboard
    recipient = Column(String(255))  # phone number, chat id, handle, email
    message = Column(String)
    status = Column(String(20), default="pending")  # pending, sent, failed
    error = Column(String)
    sent_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)


class AffiliateClick(Base):
    """Tracks outbound clicks on affiliate links for conversion/revenue analytics."""
    __tablename__ = "affiliate_clicks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    deal_id = Column(UUID(as_uuid=True), ForeignKey("arbitrage_deals.id"), nullable=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    retailer = Column(String(50))  # amazon, ebay, walmart, etc.
    original_url = Column(Text)
    affiliate_url = Column(Text)
    asin = Column(String(20), nullable=True, index=True)
    clicked_at = Column(DateTime, default=datetime.utcnow, index=True)
    converted = Column(Boolean, default=False)  # Updated later via affiliate API
    commission_earned = Column(Float, default=0.0)
