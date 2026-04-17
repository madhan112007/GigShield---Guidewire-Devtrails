from sqlalchemy import Column, String, Float, Integer, Boolean, DateTime, Enum, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
import enum
import uuid


def gen_uuid():
    return str(uuid.uuid4())


class Platform(str, enum.Enum):
    BLINKIT          = "blinkit"
    ZEPTO            = "zepto"
    SWIGGY_INSTAMART = "swiggy_instamart"
    ZOMATO           = "zomato"
    AMAZON           = "amazon"
    BIGBASKET        = "bigbasket"
    # Legacy values kept for backward compatibility with existing DB rows
    SWIGGY           = "swiggy"
    DUNZO            = "dunzo"


class PolicyTier(str, enum.Enum):
    BASIC = "basic"
    SMART = "smart"
    PRO = "pro"


class PolicyStatus(str, enum.Enum):
    ACTIVE = "active"
    EXPIRED = "expired"
    CANCELLED = "cancelled"
    PENDING = "pending"


class ClaimStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    PAID = "paid"


class DisruptionType(str, enum.Enum):
    HEAVY_RAIN = "heavy_rain"
    EXTREME_HEAT = "extreme_heat"
    AQI_SPIKE = "aqi_spike"
    TRAFFIC_DISRUPTION = "traffic_disruption"
    CIVIC_EMERGENCY = "civic_emergency"


class DisruptionSeverity(str, enum.Enum):
    MODERATE = "moderate"
    SEVERE = "severe"
    EXTREME = "extreme"


class PayoutStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"  # rollback if transfer fails mid-way


class Worker(Base):
    __tablename__ = "workers"

    id = Column(String, primary_key=True, default=gen_uuid)
    phone = Column(String(15), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(200), nullable=True)
    platform = Column(Enum(Platform), nullable=False)
    platform_worker_id = Column(String(100), nullable=True)
    city = Column(String(100), nullable=False)
    pincode = Column(String(10), nullable=False)
    upi_id = Column(String(100), nullable=True)
    bank_account = Column(String(20), nullable=True)
    bank_ifsc = Column(String(15), nullable=True)
    aadhaar_last4 = Column(String(4), nullable=True)
    is_verified = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    avg_daily_earnings = Column(Float, default=600.0)
    active_days_30 = Column(Integer, default=0, nullable=True)  # active delivery days in last 30 days
    risk_score = Column(Float, default=0.5)
    last_known_lat = Column(Float, nullable=True)
    last_known_lng = Column(Float, nullable=True)
    last_location_at = Column(DateTime(timezone=True), nullable=True)
    fcm_token = Column(String(200), nullable=True)  # Firebase push token
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    policies = relationship("Policy", back_populates="worker")
    claims = relationship("Claim", back_populates="worker")
    location_pings = relationship("WorkerLocationPing", back_populates="worker")
    notifications = relationship("WorkerNotification", back_populates="worker")


class Policy(Base):
    __tablename__ = "policies"

    id = Column(String, primary_key=True, default=gen_uuid)
    worker_id = Column(String, ForeignKey("workers.id"), nullable=False)
    tier = Column(Enum(PolicyTier), nullable=False, default=PolicyTier.SMART)
    status = Column(Enum(PolicyStatus), nullable=False, default=PolicyStatus.ACTIVE)
    weekly_premium = Column(Float, nullable=False)
    base_premium = Column(Float, nullable=False)
    max_daily_payout = Column(Float, nullable=False)
    max_weekly_payout = Column(Float, nullable=False)
    pincode = Column(String(10), nullable=False)
    city = Column(String(100), nullable=False)
    start_date = Column(DateTime(timezone=True), nullable=False)
    end_date = Column(DateTime(timezone=True), nullable=False)
    total_claimed = Column(Float, default=0.0)
    claims_count = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    worker = relationship("Worker", back_populates="policies")
    claims = relationship("Claim", back_populates="policy")


class DisruptionEvent(Base):
    __tablename__ = "disruption_events"

    id = Column(String, primary_key=True, default=gen_uuid)
    disruption_type = Column(Enum(DisruptionType), nullable=False)
    severity = Column(Enum(DisruptionSeverity), nullable=False)
    city = Column(String(100), nullable=False)
    pincode = Column(String(10), nullable=True)
    lat = Column(Float, nullable=True)
    lng = Column(Float, nullable=True)
    radius_km = Column(Float, default=5.0)  # Impact radius in km
    dss_multiplier = Column(Float, nullable=False)
    raw_value = Column(Float, nullable=True)  # mm/hr, °C, AQI value
    description = Column(Text, nullable=True)
    source = Column(String(100), nullable=True)
    started_at = Column(DateTime(timezone=True), nullable=False)
    ended_at = Column(DateTime(timezone=True), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    claims = relationship("Claim", back_populates="disruption_event")


class Claim(Base):
    __tablename__ = "claims"

    id = Column(String, primary_key=True, default=gen_uuid)
    worker_id = Column(String, ForeignKey("workers.id"), nullable=False)
    policy_id = Column(String, ForeignKey("policies.id"), nullable=False)
    disruption_event_id = Column(String, ForeignKey("disruption_events.id"), nullable=False)
    status = Column(Enum(ClaimStatus), nullable=False, default=ClaimStatus.PENDING)
    claimed_amount = Column(Float, nullable=False)
    approved_amount = Column(Float, nullable=True)
    worker_daily_avg = Column(Float, nullable=False)
    dss_multiplier = Column(Float, nullable=False)
    active_hours_ratio = Column(Float, nullable=False, default=1.0)
    fraud_score = Column(Float, default=0.0)
    fraud_flags = Column(Text, nullable=True)  # JSON string
    auto_approved = Column(Boolean, default=False)
    rejection_reason = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    processed_at = Column(DateTime(timezone=True), nullable=True)

    worker = relationship("Worker", back_populates="claims")
    policy = relationship("Policy", back_populates="claims")
    disruption_event = relationship("DisruptionEvent", back_populates="claims")
    payout = relationship("Payout", back_populates="claim", uselist=False)


class Payout(Base):
    __tablename__ = "payouts"

    id = Column(String, primary_key=True, default=gen_uuid)
    claim_id = Column(String, ForeignKey("claims.id"), nullable=False, unique=True)
    worker_id = Column(String, ForeignKey("workers.id"), nullable=False)
    amount = Column(Float, nullable=False)
    status = Column(Enum(PayoutStatus), nullable=False, default=PayoutStatus.PENDING)
    upi_id = Column(String(100), nullable=True)
    razorpay_payout_id = Column(String(100), nullable=True)
    transaction_ref = Column(String(100), nullable=True)
    initiated_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    failure_reason = Column(Text, nullable=True)
    channel = Column(String(20), default="UPI", nullable=True)
    settlement_seconds = Column(Integer, nullable=True)
    rollback_at = Column(DateTime(timezone=True), nullable=True)
    reconciled = Column(Boolean, default=False, nullable=True)

    claim = relationship("Claim", back_populates="payout")


class WorkerLocationPing(Base):
    """Stores worker GPS pings every 10 min during active hours for anti-spoofing."""
    __tablename__ = "worker_location_pings"

    id = Column(String, primary_key=True, default=gen_uuid)
    worker_id = Column(String, ForeignKey("workers.id"), nullable=False)
    lat = Column(Float, nullable=False)
    lng = Column(Float, nullable=False)
    accuracy = Column(Float, nullable=True)       # GPS accuracy in meters
    speed_kmh = Column(Float, nullable=True)      # km/h since last ping — >200 = spoof
    distance_km = Column(Float, nullable=True)    # km from last ping
    is_suspicious = Column(Boolean, default=False) # flagged if impossible movement
    city_detected = Column(String(100), nullable=True)
    pincode_detected = Column(String(10), nullable=True)
    recorded_at = Column(DateTime(timezone=True), server_default=func.now())

    worker = relationship("Worker", back_populates="location_pings")


class WorkerNotification(Base):
    """In-app notification feed — persisted for mobile app to poll."""
    __tablename__ = "worker_notifications"

    id = Column(String, primary_key=True, default=gen_uuid)
    worker_id = Column(String, ForeignKey("workers.id"), nullable=False)
    title = Column(String(120), nullable=False)
    body = Column(Text, nullable=False)
    notif_type = Column(String(40), nullable=False)  # claim_approved, claim_paid, etc.
    ref_id = Column(String(100), nullable=True)       # claim_id or event_id
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    worker = relationship("Worker", back_populates="notifications")


