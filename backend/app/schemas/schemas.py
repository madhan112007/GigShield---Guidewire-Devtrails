from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from app.models.models import Platform, PolicyTier, PolicyStatus, ClaimStatus, DisruptionType, DisruptionSeverity, PayoutStatus


# ── Auth ──────────────────────────────────────────────────────────────────────

class OTPRequest(BaseModel):
    phone: str = Field(..., pattern=r"^\+?[0-9]{10,15}$")

class OTPVerify(BaseModel):
    phone: str = Field(..., pattern=r"^\+?[0-9]{10,15}$")
    otp: str = Field(..., pattern=r"^[0-9]{6}$")

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    worker_id: Optional[str] = None
    is_new_user: bool = False
    is_dev_mode: bool = False


# ── Worker ────────────────────────────────────────────────────────────────────

class WorkerCreate(BaseModel):
    phone: Optional[str] = None
    name: str
    platform: Platform
    city: str
    pincode: str
    upi_id: Optional[str] = None
    platform_worker_id: Optional[str] = None
    avg_daily_earnings: Optional[float] = None

class WorkerUpdate(BaseModel):
    name: Optional[str] = None
    upi_id: Optional[str] = None
    bank_account: Optional[str] = None
    bank_ifsc: Optional[str] = None

class WorkerResponse(BaseModel):
    id: str
    phone: str
    name: str
    platform: Platform
    city: str
    pincode: str
    upi_id: Optional[str]
    is_verified: bool
    avg_daily_earnings: float
    risk_score: float
    created_at: datetime

    class Config:
        from_attributes = True


# ── Policy ────────────────────────────────────────────────────────────────────

class PolicyCreate(BaseModel):
    tier: PolicyTier = PolicyTier.SMART
    pincode: Optional[str] = None

class PolicyOrderResponse(BaseModel):
    order_id: str
    amount: int  # paise
    currency: str
    tier: str
    adjusted_premium: float
    key_id: str

class PolicyPaymentVerify(BaseModel):
    razorpay_order_id: str
    razorpay_payment_id: str
    razorpay_signature: str
    tier: PolicyTier
    pincode: Optional[str] = None

class PolicyResponse(BaseModel):
    id: str
    worker_id: str
    tier: PolicyTier
    status: PolicyStatus
    weekly_premium: float
    base_premium: float
    max_daily_payout: float
    max_weekly_payout: float
    pincode: str
    city: str
    start_date: datetime
    end_date: datetime
    total_claimed: float
    claims_count: int
    created_at: datetime

    class Config:
        from_attributes = True

class PremiumQuote(BaseModel):
    tier: PolicyTier
    base_premium: float
    adjusted_premium: float
    zone_risk_multiplier: float
    season_factor: float
    max_daily_payout: float
    max_weekly_payout: float
    risk_breakdown: dict


# ── Disruption Events ─────────────────────────────────────────────────────────

class DisruptionEventResponse(BaseModel):
    id: str
    disruption_type: DisruptionType
    severity: DisruptionSeverity
    city: str
    pincode: Optional[str]
    dss_multiplier: float
    raw_value: Optional[float]
    description: Optional[str]
    source: Optional[str]
    started_at: datetime
    is_active: bool

    class Config:
        from_attributes = True


# ── Claims ────────────────────────────────────────────────────────────────────

class ClaimResponse(BaseModel):
    id: str
    worker_id: str
    policy_id: str
    disruption_event_id: str
    status: ClaimStatus
    claimed_amount: float
    approved_amount: Optional[float]
    worker_daily_avg: float
    dss_multiplier: float
    active_hours_ratio: float
    fraud_score: float
    auto_approved: bool
    rejection_reason: Optional[str]
    created_at: datetime
    processed_at: Optional[datetime]

    class Config:
        from_attributes = True


# ── Payouts ───────────────────────────────────────────────────────────────────

class PayoutResponse(BaseModel):
    id: str
    claim_id: str
    worker_id: str
    amount: float
    status: PayoutStatus
    upi_id: Optional[str]
    transaction_ref: Optional[str]
    initiated_at: datetime
    completed_at: Optional[datetime]

    class Config:
        from_attributes = True


# ── Dashboard ─────────────────────────────────────────────────────────────────

class WorkerDashboard(BaseModel):
    worker: WorkerResponse
    active_policy: Optional[PolicyResponse]
    recent_claims: List[ClaimResponse]
    total_earned_protection: float
    active_disruptions: List[DisruptionEventResponse]
