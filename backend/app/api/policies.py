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
    key_id, key_secret = _active_keys()
    return razorpay.Client(auth=(key_id, key_secret))


def _active_keys() -> tuple[str, str]:
    """Returns (key_id, key_secret) — live keys in production, test keys in dev."""
    if (
        settings.ENVIRONMENT == "production"
        and settings.RAZORPAY_LIVE_KEY_ID.startswith("rzp_live_")
        and settings.RAZORPAY_LIVE_KEY_SECRET
    ):
        return settings.RAZORPAY_LIVE_KEY_ID, settings.RAZORPAY_LIVE_KEY_SECRET
    return settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET


def _is_mock():
    key_id, _ = _active_keys()
    return key_id == "rzp_test_mock"


@router.post("/create-order", response_model=PolicyOrderResponse)
async def create_order(
    payload: PolicyCreate,
    db: AsyncSession = Depends(get_db),
    current_worker: Worker = Depends(get_current_worker),
):
    from sqlalchemy import func
    from app.models.models import Claim, ClaimStatus
    from datetime import timedelta

    now = datetime.now(timezone.utc)
    pincode = payload.pincode or current_worker.pincode

    # Compute the same discount inputs used by /quote so the order amount matches
    no_claims_weeks = 0
    for week in range(1, 13):
        week_start = now - timedelta(weeks=week)
        week_end   = now - timedelta(weeks=week - 1)
        claims_in_week = await db.execute(
            select(func.count(Claim.id)).where(
                Claim.worker_id == current_worker.id,
                Claim.created_at >= week_start,
                Claim.created_at < week_end,
                Claim.status.in_([ClaimStatus.APPROVED, ClaimStatus.PAID]),
            )
        )
        if (claims_in_week.scalar() or 0) == 0:
            no_claims_weeks += 1
        else:
            break

    policy_count_result = await db.execute(
        select(func.count(Policy.id)).where(Policy.worker_id == current_worker.id)
    )
    policy_count = policy_count_result.scalar() or 1

    twelve_weeks_ago = now - timedelta(weeks=12)
    actual_claims_result = await db.execute(
        select(func.count(Claim.id)).where(
            Claim.worker_id == current_worker.id,
            Claim.created_at >= twelve_weeks_ago,
            Claim.status.in_([ClaimStatus.APPROVED, ClaimStatus.PAID]),
        )
    )
    actual_claims_12w = actual_claims_result.scalar() or 0
    worker_history_factor = 0.90 if actual_claims_12w == 0 else round(
        max(0.85, min(1.30, actual_claims_12w / 6.0)), 3
    )

    premium_data = await calculate_premium(
        tier=payload.tier,
        pincode=pincode,
        city=current_worker.city,
        worker_history_factor=worker_history_factor,
        platform_activity_score=1.0,
        no_claims_weeks=no_claims_weeks,
        policy_count=policy_count,
    )
    amount_paise = int(premium_data["adjusted_premium"] * 100)
    key_id, _ = _active_keys()

    if _is_mock():
        return PolicyOrderResponse(
            order_id=f"order_mock_{payload.tier.value}",
            amount=amount_paise,
            currency="INR",
            tier=payload.tier.value,
            adjusted_premium=premium_data["adjusted_premium"],
            key_id=key_id,
        )

    client = _razorpay_client()
    order = client.order.create({
        "amount": amount_paise,
        "currency": "INR",
        "payment_capture": 1,
        "notes": {"worker_id": current_worker.id, "tier": payload.tier.value},
    })

    return PolicyOrderResponse(
        order_id=order["id"],
        amount=amount_paise,
        currency="INR",
        tier=payload.tier.value,
        adjusted_premium=premium_data["adjusted_premium"],
        key_id=key_id,
    )


@router.post("/verify-payment", response_model=PolicyResponse)
async def verify_payment(
    payload: PolicyPaymentVerify,
    db: AsyncSession = Depends(get_db),
    current_worker: Worker = Depends(get_current_worker),
):
    # Verify Razorpay signature using the active secret (live or test)
    _, key_secret = _active_keys()
    body = f"{payload.razorpay_order_id}|{payload.razorpay_payment_id}"
    expected = hmac.new(
        key_secret.encode(),
        body.encode(),
        hashlib.sha256,
    ).hexdigest()

    if expected != payload.razorpay_signature:
        raise HTTPException(status_code=400, detail="Payment verification failed")

    return await _activate_policy(payload.tier, payload.pincode, current_worker, db)


@router.get("/available-coverage")
async def get_available_coverage(
    city: str = "",
    current_worker: Worker = Depends(get_current_worker),
):
    """
    Returns which disruption types are covered per tier for this worker's city.
    Used by mobile app to show city-specific coverage at policy purchase.
    """
    from app.api.claims import CITY_POOLS
    from app.models.models import DisruptionType
    from app.services.actuarial_service import TIER_PERILS, TRIGGER_PROBABILITY, DEFAULT_TRIGGER_PROB

    target_city = city or current_worker.city
    covered_types = CITY_POOLS.get(target_city, list(DisruptionType))
    city_probs = TRIGGER_PROBABILITY.get(target_city, DEFAULT_TRIGGER_PROB)

    tiers = {}
    for tier in PolicyTier:
        from app.services.actuarial_service import TIER_PERILS
        tier_perils = TIER_PERILS[tier]
        tiers[tier.value] = {
            "base_premium": BASE_PREMIUMS[tier],
            "max_daily_payout": MAX_DAILY_PAYOUT[tier],
            "max_weekly_payout": MAX_WEEKLY_PAYOUT[tier],
            "covered_perils": [
                {
                    "type": p,
                    "covered_in_city": any(p in ct.value for ct in covered_types),
                    "annual_trigger_probability_pct": round(city_probs.get(p, 0.05) * 100, 1),
                }
                for p in tier_perils
            ],
        }
    return {"city": target_city, "tiers": tiers}


@router.get("/quote", response_model=PremiumQuote)
async def get_quote(
    tier: PolicyTier = PolicyTier.SMART,
    db: AsyncSession = Depends(get_db),
    current_worker: Worker = Depends(get_current_worker),
):
    import asyncio
    from sqlalchemy import func
    from app.models.models import Claim, ClaimStatus
    from datetime import timedelta

    now = datetime.now(timezone.utc)

    # Query real no-claims streak from DB
    no_claims_weeks = 0
    for week in range(1, 13):
        week_start = now - timedelta(weeks=week)
        week_end   = now - timedelta(weeks=week - 1)
        claims_in_week = await db.execute(
            select(func.count(Claim.id)).where(
                Claim.worker_id == current_worker.id,
                Claim.created_at >= week_start,
                Claim.created_at < week_end,
                Claim.status.in_([ClaimStatus.APPROVED, ClaimStatus.PAID]),
            )
        )
        if (claims_in_week.scalar() or 0) == 0:
            no_claims_weeks += 1
        else:
            break

    # Query real policy count (loyalty discount)
    policy_count_result = await db.execute(
        select(func.count(Policy.id)).where(Policy.worker_id == current_worker.id)
    )
    policy_count = policy_count_result.scalar() or 1

    # Worker history factor from last 12 weeks of claims
    twelve_weeks_ago = now - timedelta(weeks=12)
    actual_claims_result = await db.execute(
        select(func.count(Claim.id)).where(
            Claim.worker_id == current_worker.id,
            Claim.created_at >= twelve_weeks_ago,
            Claim.status.in_([ClaimStatus.APPROVED, ClaimStatus.PAID]),
        )
    )
    actual_claims_12w = actual_claims_result.scalar() or 0
    EXPECTED_CLAIMS_12W = 6.0
    worker_history_factor = 0.90 if actual_claims_12w == 0 else round(
        max(0.85, min(1.30, actual_claims_12w / EXPECTED_CLAIMS_12W)), 3
    )

    try:
        result = await asyncio.wait_for(
            calculate_premium(
                tier=tier,
                pincode=current_worker.pincode,
                city=current_worker.city,
                worker_history_factor=worker_history_factor,
                platform_activity_score=1.0,
                no_claims_weeks=no_claims_weeks,
                policy_count=policy_count,
            ),
            timeout=5.0,
        )
    except asyncio.TimeoutError:
        from app.services.premium_service import get_season_factor, get_sub_zone_risk
        base = BASE_PREMIUMS[tier]
        zone_risk = get_sub_zone_risk(current_worker.pincode)
        season = get_season_factor()
        no_claims_discount = min(0.15, (no_claims_weeks // 4) * 0.05)
        loyalty_discount = min(0.08, (max(0, policy_count - 1)) * 0.04)
        adjusted = round(base * zone_risk * season * worker_history_factor * (1 - no_claims_discount - loyalty_discount), 2)
        result = {
            "tier": tier,
            "base_premium": base,
            "adjusted_premium": adjusted,
            "zone_risk_multiplier": zone_risk,
            "season_factor": season,
            "worker_history_factor": worker_history_factor,
            "platform_activity_score": 1.0,
            "no_claims_discount": round(no_claims_discount * 100, 1),
            "loyalty_discount": round(loyalty_discount * 100, 1),
            "total_discount_pct": round((no_claims_discount + loyalty_discount) * 100, 1),
            "max_daily_payout": MAX_DAILY_PAYOUT[tier],
            "max_weekly_payout": MAX_WEEKLY_PAYOUT[tier],
            "risk_breakdown": {
                "base": base,
                "after_zone": round(base * zone_risk, 2),
                "after_season": round(base * zone_risk * season, 2),
                "after_discounts": adjusted,
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

    # Feedback loop: count past policies and claim-free weeks for discounts
    policy_count_result = await db.execute(
        select(func.count(Policy.id)).where(Policy.worker_id == worker.id)
    )
    policy_count = policy_count_result.scalar() or 1

    # Count consecutive claim-free weeks (look back up to 12 weeks)
    no_claims_weeks = 0
    for week in range(1, 13):
        week_start = now - timedelta(weeks=week)
        week_end   = now - timedelta(weeks=week - 1)
        claims_in_week = await db.execute(
            select(func.count(Claim.id)).where(
                Claim.worker_id == worker.id,
                Claim.created_at >= week_start,
                Claim.created_at < week_end,
                Claim.status.in_([ClaimStatus.APPROVED, ClaimStatus.PAID]),
            )
        )
        if (claims_in_week.scalar() or 0) == 0:
            no_claims_weeks += 1
        else:
            break  # streak broken

    # Worker history factor: ratio of actual claims paid vs actuarial expectation.
    # If worker has claimed more than expected (high-risk), premium goes up.
    # If worker has claimed less (low-risk), premium goes down.
    # Clamped to [0.85, 1.30] to prevent extreme swings.
    twelve_weeks_ago = now - timedelta(weeks=12)
    actual_claims_result = await db.execute(
        select(func.count(Claim.id)).where(
            Claim.worker_id == worker.id,
            Claim.created_at >= twelve_weeks_ago,
            Claim.status.in_([ClaimStatus.APPROVED, ClaimStatus.PAID]),
        )
    )
    actual_claims_12w = actual_claims_result.scalar() or 0
    # Actuarial expectation: ~0.5 claims/week for an average worker = 6 over 12 weeks
    EXPECTED_CLAIMS_12W = 6.0
    if actual_claims_12w == 0:
        worker_history_factor = 0.90  # no claims = lower risk = discount
    else:
        worker_history_factor = round(
            max(0.85, min(1.30, actual_claims_12w / EXPECTED_CLAIMS_12W)), 3
        )

    pincode = pincode_override or worker.pincode
    premium_data = await calculate_premium(
        tier=tier,
        pincode=pincode,
        city=worker.city,
        no_claims_weeks=no_claims_weeks,
        policy_count=policy_count,
        worker_history_factor=worker_history_factor,
    )

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
