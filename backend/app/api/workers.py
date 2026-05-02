from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.models import Worker, Policy, Claim, DisruptionEvent, PolicyStatus
from app.schemas.schemas import WorkerCreate, WorkerUpdate, WorkerResponse, WorkerDashboard
from app.services.auth_service import get_current_worker
from app.services.platform_service import fetch_platform_earnings
from datetime import datetime, timezone

router = APIRouter()


@router.post("/register", response_model=WorkerResponse)
async def register_worker(
    payload: WorkerCreate,
    db: AsyncSession = Depends(get_db),
    current_worker: Worker = Depends(get_current_worker),
):
    """Complete worker registration — auto-fetches avg earnings from platform API"""
    current_worker.name = payload.name
    current_worker.platform = payload.platform
    current_worker.city = payload.city
    current_worker.pincode = payload.pincode
    current_worker.upi_id = payload.upi_id
    current_worker.platform_worker_id = payload.platform_worker_id

    # Auto-fetch avg daily earnings from platform using worker's phone number
    earnings_data = await fetch_platform_earnings(
        phone=current_worker.phone,
        platform=payload.platform.value,
        city=payload.city,
    )
    current_worker.avg_daily_earnings = earnings_data["avg_daily_earnings"]
    current_worker.active_days_30 = earnings_data.get("active_days_30", 0)

    # Underwriting rule: minimum 7 active delivery days before cover eligibility
    current_worker.is_verified = current_worker.active_days_30 >= 7
    await db.commit()
    await db.refresh(current_worker)
    return current_worker


@router.get("/platform-earnings", response_model=dict)
async def get_platform_earnings(
    platform: str,
    current_worker: Worker = Depends(get_current_worker),
):
    """Fetch earnings data from the worker's platform using their phone number.
    Called during onboarding to show the worker what earnings were detected."""
    return await fetch_platform_earnings(
        phone=current_worker.phone,
        platform=platform,
    )


@router.get("/me", response_model=WorkerResponse)
async def get_me(current_worker: Worker = Depends(get_current_worker)):
    return current_worker


@router.patch("/me", response_model=WorkerResponse)
async def update_me(
    payload: WorkerUpdate,
    db: AsyncSession = Depends(get_db),
    current_worker: Worker = Depends(get_current_worker),
):
    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(current_worker, field, value)
    await db.commit()
    await db.refresh(current_worker)
    return current_worker


@router.post("/fcm-token")
async def register_fcm_token(
    payload: dict,
    db: AsyncSession = Depends(get_db),
    current_worker: Worker = Depends(get_current_worker),
):
    """Register or refresh FCM push token for this device."""
    token = payload.get("fcm_token", "").strip()
    if not token:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="fcm_token is required")
    current_worker.fcm_token = token
    await db.commit()
    return {"ok": True}


@router.get("/dashboard", response_model=WorkerDashboard)
async def get_dashboard(
    db: AsyncSession = Depends(get_db),
    current_worker: Worker = Depends(get_current_worker),
):
    """Get worker dashboard data"""
    from datetime import datetime, timezone

    now = datetime.now(timezone.utc)
    result = await db.execute(
        select(Policy).where(
            Policy.worker_id == current_worker.id,
            Policy.status == PolicyStatus.ACTIVE,
        ).order_by(Policy.created_at.desc())
    )
    all_policies = result.scalars().all()
    active_policy = None
    for p in all_policies:
        end = p.end_date.replace(tzinfo=timezone.utc) if p.end_date.tzinfo is None else p.end_date
        if end >= now:
            active_policy = p
            break

    # Recent claims (last 5)
    result = await db.execute(
        select(Claim)
        .where(Claim.worker_id == current_worker.id)
        .order_by(Claim.created_at.desc())
        .limit(5)
    )
    recent_claims = result.scalars().all()

    # Total earned protection (sum of all approved/paid payouts, not just last 5)
    from sqlalchemy import func
    from app.models.models import ClaimStatus
    total_result = await db.execute(
        select(func.coalesce(func.sum(Claim.approved_amount), 0.0)).where(
            Claim.worker_id == current_worker.id,
            Claim.status.in_([ClaimStatus.APPROVED, ClaimStatus.PAID]),
        )
    )
    total_protection = float(total_result.scalar() or 0)

    # Active disruptions in worker's city
    result = await db.execute(
        select(DisruptionEvent).where(
            DisruptionEvent.city == current_worker.city,
            DisruptionEvent.is_active == True,
        )
    )
    active_disruptions = result.scalars().all()

    return WorkerDashboard(
        worker=current_worker,
        active_policy=active_policy,
        recent_claims=recent_claims,
        total_earned_protection=total_protection,
        active_disruptions=active_disruptions,
    )
