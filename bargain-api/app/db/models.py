from sqlalchemy import Column, String, DateTime, Numeric, Boolean, JSON, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID
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
    refresh_token = Column(String(255))
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
    asin = Column(String(20), nullable=False, index=True)
    title = Column(String(500), nullable=False)
    image_url = Column(String(1000))
    buy_url = Column(String(1000))
    buy_platform = Column(String(50), default="amazon")
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
