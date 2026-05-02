from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timedelta, timezone
import razorpay
import hmac
import hashlib
from app.database import get_db
from app.models.models import Worker, Policy, PolicyStatus, PolicyTier
from app.schemas.schemas import PolicyCreate, PolicyResponse, PremiumQuote, PolicyOrderResponse, PolicyPaymentVerify
from app.services.auth_service import get_current_worker, get_current_auth_context, AuthContext
from app.services.premium_service import calculate_premium, BASE_PREMIUMS, MAX_DAILY_PAYOUT, MAX_WEEKLY_PAYOUT
from app.config import settings

router = APIRouter()


def _razorpay_client():
    return razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))


def _is_mock():
    return settings.RAZORPAY_KEY_ID == "rzp_test_mock"


@router.post("/create-order", response_model=PolicyOrderResponse)
async def create_order(
    payload: PolicyCreate,
    current_worker: Worker = Depends(get_current_worker),
):
    pincode = payload.pincode or current_worker.pincode
    premium_data = await calculate_premium(tier=payload.tier, pincode=pincode, city=current_worker.city)
    amount_paise = int(premium_data["adjusted_premium"] * 100)

    if _is_mock():
        # Return a fake order so the Flutter SDK still opens (test mode only)
        return PolicyOrderResponse(
            order_id=f"order_mock_{payload.tier.value}",
            amount=amount_paise,
            currency="INR",
            tier=payload.tier.value,
            adjusted_premium=premium_data["adjusted_premium"],
            key_id=settings.RAZORPAY_KEY_ID,
        )

    client = _razorpay_client()
    order = client.order.create({
        "amount": amount_paise,
        "currency": "INR",
        "payment_capture": 1,
        "notes": {
            "worker_id": current_worker.id,
            "tier": payload.tier.value,
        }
    })

    return PolicyOrderResponse(
        order_id=order["id"],
        amount=amount_paise,
        currency="INR",
        tier=payload.tier.value,
        adjusted_premium=premium_data["adjusted_premium"],
        key_id=settings.RAZORPAY_KEY_ID,
    )


@router.post("/verify-payment", response_model=PolicyResponse)
async def verify_payment(
    payload: PolicyPaymentVerify,
    db: AsyncSession = Depends(get_db),
    current_worker: Worker = Depends(get_current_worker),
):
    # Verify Razorpay signature
    body = f"{payload.razorpay_order_id}|{payload.razorpay_payment_id}"
    expected = hmac.new(
        settings.RAZORPAY_KEY_SECRET.encode(),
        body.encode(),
        hashlib.sha256,
    ).hexdigest()

    if expected != payload.razorpay_signature:
        raise HTTPException(status_code=400, detail="Payment verification failed")

    return await _activate_policy(payload.tier, payload.pincode, current_worker, db)


@router.get("/quote", response_model=PremiumQuote)
async def get_quote(
    tier: PolicyTier = PolicyTier.SMART,
    current_worker: Worker = Depends(get_current_worker),
):
    import asyncio
    try:
        result = await asyncio.wait_for(
            calculate_premium(
                tier=tier,
                pincode=current_worker.pincode,
                city=current_worker.city,
                worker_history_factor=1.0,
                platform_activity_score=1.0,
            ),
            timeout=5.0,
        )
    except asyncio.TimeoutError:
        # Gemini timed out — return rule-based fallback immediately
        from app.services.premium_service import get_season_factor, get_sub_zone_risk, MAX_DAILY_PAYOUT, MAX_WEEKLY_PAYOUT
        base = BASE_PREMIUMS[tier]
        zone_risk = get_sub_zone_risk(current_worker.pincode)
        season = get_season_factor()
        adjusted = round(base * zone_risk * season, 2)
        result = {
            "tier": tier,
            "base_premium": base,
            "adjusted_premium": adjusted,
            "zone_risk_multiplier": zone_risk,
            "season_factor": season,
            "worker_history_factor": 1.0,
            "platform_activity_score": 1.0,
            "max_daily_payout": MAX_DAILY_PAYOUT[tier],
            "max_weekly_payout": MAX_WEEKLY_PAYOUT[tier],
            "risk_breakdown": {
                "base": base,
                "after_zone": round(base * zone_risk, 2),
                "after_season": round(base * zone_risk * season, 2),
                "final": adjusted,
            },
        }
    return PremiumQuote(**result)


@router.post("/", response_model=PolicyResponse)
async def create_policy(
    payload: PolicyCreate,
    db: AsyncSession = Depends(get_db),
    auth: AuthContext = Depends(get_current_auth_context),
):
    """Direct policy creation — used in dev/mock mode bypassing Razorpay."""
    if not settings.DEMO_MODE_ENABLED or not auth.is_dev_mode or settings.ENVIRONMENT == "production":
        raise HTTPException(status_code=403, detail="Direct policy creation is available only in dev mode")
    return await _activate_policy(payload.tier, payload.pincode, auth.worker, db)


@router.get("/", response_model=list[PolicyResponse])
async def list_policies(
    db: AsyncSession = Depends(get_db),
    current_worker: Worker = Depends(get_current_worker),
):
    result = await db.execute(
        select(Policy)
        .where(Policy.worker_id == current_worker.id)
        .order_by(Policy.created_at.desc())
    )
    return result.scalars().all()


@router.get("/active", response_model=PolicyResponse)
async def get_active_policy(
    db: AsyncSession = Depends(get_db),
    current_worker: Worker = Depends(get_current_worker),
):
    now = datetime.now(timezone.utc)
    # Try active + not expired first
    result = await db.execute(
        select(Policy).where(
            Policy.worker_id == current_worker.id,
            Policy.status == PolicyStatus.ACTIVE,
        ).order_by(Policy.created_at.desc())
    )
    policy = result.scalars().first()
    if not policy:
        raise HTTPException(status_code=404, detail="No active policy found")
    # Auto-fix: if end_date is timezone-naive, make it aware
    end_date = policy.end_date
    if end_date.tzinfo is None:
        from datetime import timezone as tz
        end_date = end_date.replace(tzinfo=tz.utc)
    if end_date < now:
        policy.status = PolicyStatus.EXPIRED
        await db.commit()
        raise HTTPException(status_code=404, detail="No active policy found")
    return policy


async def _activate_policy(tier, pincode_override, worker: Worker, db: AsyncSession) -> Policy:
    """Expire any existing active policy, then create and return a new one."""
    from sqlalchemy import func
    from app.models.models import Claim, ClaimStatus

    now = datetime.now(timezone.utc)
    existing = await db.execute(
        select(Policy).where(
            Policy.worker_id == worker.id,
            Policy.status == PolicyStatus.ACTIVE,
            Policy.end_date >= now,
        )
    )
    old = existing.scalar_one_or_none()
    if old:
        old.status = PolicyStatus.EXPIRED
        old.end_date = now
        await db.flush()

    pincode = pincode_override or worker.pincode
    premium_data = await calculate_premium(tier=tier, pincode=pincode, city=worker.city)

    policy = Policy(
        worker_id=worker.id,
        tier=tier,
        status=PolicyStatus.ACTIVE,
        weekly_premium=premium_data["adjusted_premium"],
        base_premium=premium_data["base_premium"],
        max_daily_payout=premium_data["max_daily_payout"],
        max_weekly_payout=premium_data["max_weekly_payout"],
        pincode=pincode,
        city=worker.city,
        start_date=now,
        end_date=now + timedelta(days=7),
    )
    db.add(policy)
    await db.commit()
    await db.refresh(policy)
    return policy
