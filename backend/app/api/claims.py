from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime, timedelta, timezone
from app.database import get_db
from app.models.models import Worker, Policy, Claim, DisruptionEvent, Payout, PolicyStatus, ClaimStatus, PayoutStatus, DisruptionType
from app.schemas.schemas import ClaimResponse
from app.services.auth_service import get_current_worker
from app.services.premium_service import calculate_payout, MAX_DAILY_PAYOUT, MAX_WEEKLY_PAYOUT
from app.services.fraud_service import calculate_fraud_score
from app.services.infra_service import get_infra_adjusted_dss
from app.services.payout_service import initiate_upi_payout
from app.services.notification_service import notify_claim_approved, notify_claim_rejected, notify_claim_paid

router = APIRouter()

# City pools — which disruption types are valid per city
# Delhi/NCR: AQI + Heat pool | Mumbai/Bangalore: Rain pool | All: Civic + Traffic
CITY_POOLS = {
    "Delhi":          [DisruptionType.AQI_SPIKE, DisruptionType.EXTREME_HEAT, DisruptionType.TRAFFIC_DISRUPTION, DisruptionType.CIVIC_EMERGENCY],
    "Mumbai":         [DisruptionType.HEAVY_RAIN, DisruptionType.TRAFFIC_DISRUPTION, DisruptionType.CIVIC_EMERGENCY],
    "Bangalore":      [DisruptionType.HEAVY_RAIN, DisruptionType.AQI_SPIKE, DisruptionType.TRAFFIC_DISRUPTION, DisruptionType.CIVIC_EMERGENCY],
    "Chennai":        [DisruptionType.HEAVY_RAIN, DisruptionType.EXTREME_HEAT, DisruptionType.CIVIC_EMERGENCY],
    "Hyderabad":      [DisruptionType.HEAVY_RAIN, DisruptionType.EXTREME_HEAT, DisruptionType.TRAFFIC_DISRUPTION, DisruptionType.CIVIC_EMERGENCY],
    "Coimbatore":     [DisruptionType.HEAVY_RAIN, DisruptionType.EXTREME_HEAT, DisruptionType.TRAFFIC_DISRUPTION, DisruptionType.CIVIC_EMERGENCY],
    "Tiruchirappalli":[DisruptionType.HEAVY_RAIN, DisruptionType.EXTREME_HEAT, DisruptionType.CIVIC_EMERGENCY],
    "Madurai":        [DisruptionType.HEAVY_RAIN, DisruptionType.EXTREME_HEAT, DisruptionType.CIVIC_EMERGENCY],
    "Salem":          [DisruptionType.HEAVY_RAIN, DisruptionType.EXTREME_HEAT, DisruptionType.CIVIC_EMERGENCY],
    "Pune":           [DisruptionType.HEAVY_RAIN, DisruptionType.TRAFFIC_DISRUPTION, DisruptionType.CIVIC_EMERGENCY],
    "Kolkata":        [DisruptionType.HEAVY_RAIN, DisruptionType.AQI_SPIKE, DisruptionType.CIVIC_EMERGENCY],
    "Ahmedabad":      [DisruptionType.EXTREME_HEAT, DisruptionType.AQI_SPIKE, DisruptionType.TRAFFIC_DISRUPTION, DisruptionType.CIVIC_EMERGENCY],
    "Lucknow":        [DisruptionType.EXTREME_HEAT, DisruptionType.AQI_SPIKE, DisruptionType.TRAFFIC_DISRUPTION, DisruptionType.CIVIC_EMERGENCY],
    "Patna":          [DisruptionType.HEAVY_RAIN, DisruptionType.EXTREME_HEAT, DisruptionType.CIVIC_EMERGENCY],
}

# Active hours: delivery workers operate 6am-10pm IST
ACTIVE_HOUR_START = 6
ACTIVE_HOUR_END = 22


def is_within_active_hours(dt: datetime) -> bool:
    """Check if event occurred during worker active hours (6am-10pm IST)"""
    ist_hour = (dt.hour + 5) % 24  # UTC+5:30 approx
    return ACTIVE_HOUR_START <= ist_hour < ACTIVE_HOUR_END


def active_hours_ratio(event_started_at: datetime) -> float:
    """Returns ratio of remaining active hours after event start."""
    ist_hour = (event_started_at.hour + 5) % 24
    if ist_hour < ACTIVE_HOUR_START or ist_hour >= ACTIVE_HOUR_END:
        return 0.5  # outside active hours — use 50% default so demo always works
    remaining = ACTIVE_HOUR_END - ist_hour
    total_active = ACTIVE_HOUR_END - ACTIVE_HOUR_START
    return round(remaining / total_active, 2)


import math

def haversine(lat1, lon1, lat2, lon2):
    """Calculate distance in km between two points."""
    R = 6371  # Earth radius in km
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

@router.post("/trigger/{disruption_event_id}", response_model=ClaimResponse)
async def trigger_claim(
    disruption_event_id: str,
    db: AsyncSession = Depends(get_db),
    current_worker: Worker = Depends(get_current_worker),
):
    now = datetime.now(timezone.utc)

    # Get active policy with row-level locking to prevent race conditions
    result = await db.execute(
        select(Policy).where(
            Policy.worker_id == current_worker.id,
            Policy.status == PolicyStatus.ACTIVE,
        ).order_by(Policy.created_at.desc())
        .with_for_update()
    )
    all_active = result.scalars().all()
    policy = None
    for p in all_active:
        end = p.end_date.replace(tzinfo=timezone.utc) if p.end_date.tzinfo is None else p.end_date
        if end >= now:
            policy = p
            break
    if not policy:
        raise HTTPException(status_code=400, detail="No active policy found")
    
    # Ensure policy end_date is timezone-aware
    end_date = policy.end_date
    if end_date.tzinfo is None:
        end_date = end_date.replace(tzinfo=timezone.utc)
        
    if end_date < now:
        policy.status = PolicyStatus.EXPIRED
        await db.commit()
        raise HTTPException(status_code=400, detail="Policy has expired")

    # Get disruption event
    result = await db.execute(select(DisruptionEvent).where(DisruptionEvent.id == disruption_event_id))
    event = result.scalar_one_or_none()
    if not event:
        raise HTTPException(status_code=404, detail="Disruption event not found")

    if event.city.lower() != current_worker.city.lower():
        raise HTTPException(status_code=400, detail="Disruption event is not in your city")

    # City pool check
    allowed_types = CITY_POOLS.get(current_worker.city, list(DisruptionType))
    if event.disruption_type not in allowed_types:
        raise HTTPException(status_code=400, detail=f"{event.disruption_type} is not covered in {current_worker.city} pool")

    # Active hours check
    event_started_at = event.started_at
    if event_started_at.tzinfo is None:
        event_started_at = event_started_at.replace(tzinfo=timezone.utc)
    
    hours_ratio = active_hours_ratio(event_started_at)
    if hours_ratio <= 0.0:
        hours_ratio = 0.5  # fallback for outside-hours events

    # ── Dark Store Proximity / Ward-level check ─────────────────────────────
    worker_prefix = current_worker.pincode[:3] if current_worker.pincode else ""
    event_prefix = (event.pincode or "")[:3]
    
    # Base proximity factor
    proximity_factor = 1.0
    
    # From app.models.models import WorkerLocationPing
    from app.models.models import WorkerLocationPing
    
    # Use GPS coordinates if available for precise proximity
    last_ping_result = await db.execute(
        select(WorkerLocationPing).where(
            WorkerLocationPing.worker_id == current_worker.id,
        ).order_by(WorkerLocationPing.recorded_at.desc()).limit(1)
    )
    last_ping = last_ping_result.scalar_one_or_none()
    
    if last_ping and event.lat and event.lng:
        distance = haversine(last_ping.lat, last_ping.lng, event.lat, event.lng)
        # Radius check: if outside 10km, reduce payout significantly
        # If within radius_km, full payout. If between radius and 2*radius, partial.
        radius = event.radius_km or 5.0
        if distance <= radius:
            proximity_factor = 1.0
        elif distance <= radius * 2:
            proximity_factor = 0.7
        else:
            proximity_factor = 0.4
    elif event_prefix and worker_prefix and worker_prefix != event_prefix:
        # Fallback to pincode ward check if GPS not available
        proximity_factor = 0.7
    else:
        proximity_factor = 1.0

    # Duplicate claim check
    dup = await db.execute(
        select(Claim).where(
            Claim.worker_id == current_worker.id,
            Claim.disruption_event_id == disruption_event_id,
        )
    )
    if dup.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Already claimed this disruption event")

    # Claims this week
    week_ago = now - timedelta(days=7)
    count_result = await db.execute(
        select(func.count(Claim.id)).where(
            Claim.worker_id == current_worker.id,
            Claim.created_at >= week_ago,
        )
    )
    claims_this_week = count_result.scalar() or 0

    # Worker's historical average claims per week (last 12 weeks)
    twelve_weeks_ago = now - timedelta(weeks=12)
    hist_result = await db.execute(
        select(func.count(Claim.id)).where(
            Claim.worker_id == current_worker.id,
            Claim.created_at >= twelve_weeks_ago,
        )
    )
    hist_count = hist_result.scalar() or 0
    worker_avg_claims_per_week = round(hist_count / 12.0, 2) if hist_count > 0 else 0.0

    # Zone-level stats: how many workers in same pincode zone claimed this event
    zone_prefix = current_worker.pincode[:3] if current_worker.pincode else ""
    zone_claims_result = await db.execute(
        select(func.count(Claim.id)).where(
            Claim.disruption_event_id == disruption_event_id,
        ).join(Worker).where(Worker.pincode.like(f"{zone_prefix}%"))
    )
    zone_claim_count = zone_claims_result.scalar() or 0

    # Total active workers in zone
    zone_workers_result = await db.execute(
        select(func.count(Worker.id)).where(
            Worker.pincode.like(f"{zone_prefix}%"),
            Worker.is_active == True,
        )
    )
    zone_total_workers = zone_workers_result.scalar() or 0

    # Fraud detection (re-uses last_ping if fetched)
    ping_cutoff = now - timedelta(minutes=30)
    suspicious_result = await db.execute(
        select(WorkerLocationPing).where(
            WorkerLocationPing.worker_id == current_worker.id,
            WorkerLocationPing.is_suspicious == True,
            WorkerLocationPing.recorded_at >= ping_cutoff,
        ).limit(1)
    )
    had_suspicious_ping = suspicious_result.scalar_one_or_none() is not None
    last_known_city = last_ping.city_detected if last_ping else ""

    fraud_result = calculate_fraud_score(
        worker_city=current_worker.city,
        event_city=event.city,
        worker_pincode=current_worker.pincode,
        event_pincode=event.pincode or "",
        was_platform_active=True,
        claims_this_week=claims_this_week,
        claims_same_event=0,
        event_started_at=event_started_at,
        claim_created_at=now,
        disruption_type=event.disruption_type,
        last_known_city=last_known_city,
        had_suspicious_ping=had_suspicious_ping,
        active_hours_ratio=hours_ratio,
        claim_amount_ratio=1.0,
        worker_avg_claims_per_week=worker_avg_claims_per_week,
        zone_avg_claims_per_event=0.0,
        zone_claim_count_this_event=zone_claim_count,
        zone_total_workers=zone_total_workers,
    )

    # Cap management
    weekly_cap = MAX_WEEKLY_PAYOUT[policy.tier]
    weekly_claimed = float(policy.total_claimed or 0)
    weekly_remaining = max(0.0, weekly_cap - weekly_claimed)

    if weekly_remaining <= 0:
        raise HTTPException(status_code=400, detail="Weekly payout cap reached for this policy")

    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    today_result = await db.execute(
        select(func.coalesce(func.sum(Claim.approved_amount), 0.0)).where(
            Claim.worker_id == current_worker.id,
            Claim.status.in_([ClaimStatus.APPROVED, ClaimStatus.PAID]),
            Claim.created_at >= today_start,
        )
    )
    claimed_today = float(today_result.scalar() or 0)

    daily_cap = MAX_DAILY_PAYOUT[policy.tier]
    daily_remaining = max(0.0, daily_cap - claimed_today)
    effective_cap = min(daily_remaining, weekly_remaining)

    effective_hours_ratio = hours_ratio * proximity_factor

    # ── Ward-level infra-adjusted DSS ────────────────────────────────────────
    # Use worker's actual GPS location if available, else registered pincode
    gps_city = last_ping.city_detected if last_ping else current_worker.city
    gps_pincode = last_ping.pincode_detected if last_ping else current_worker.pincode
    actual_city = gps_city or current_worker.city
    actual_pincode = gps_pincode or current_worker.pincode

    adjusted_dss, infra_hours_ratio, infra_score = await get_infra_adjusted_dss(
        base_dss=event.dss_multiplier,
        city=actual_city,
        pincode=actual_pincode,
        disruption_type=event.disruption_type.value,
        severity=event.severity.value,
    )

    # Final effective hours ratio:
    # infra_hours_ratio = how long disruption actually blocks worker in this ward
    # proximity_factor = how close worker is to epicenter
    # We take the more conservative (lower) of infra-based and time-of-day based
    effective_hours_ratio = round(
        min(hours_ratio, infra_hours_ratio) * proximity_factor, 3
    )

    payout_data = calculate_payout(
        worker_daily_avg=current_worker.avg_daily_earnings,
        dss_multiplier=adjusted_dss,
        active_hours_ratio=effective_hours_ratio,
        tier=policy.tier,
        existing_claimed_today=claimed_today,
    )
        worker_daily_avg=current_worker.avg_daily_earnings,
        dss_multiplier=adjusted_dss,
        active_hours_ratio=effective_hours_ratio,
        tier=policy.tier,
        existing_claimed_today=claimed_today,
    )

    claim = Claim(
        worker_id=current_worker.id,
        policy_id=policy.id,
        disruption_event_id=event.id,
        status=ClaimStatus.PENDING,
        claimed_amount=payout_data["raw_payout"],
        worker_daily_avg=current_worker.avg_daily_earnings,
        dss_multiplier=adjusted_dss,
        active_hours_ratio=effective_hours_ratio,
        fraud_score=fraud_result["fraud_score"],
        fraud_flags=fraud_result["flags_json"],
        auto_approved=fraud_result["auto_approve"],
    )

    if fraud_result["auto_approve"]:
        approved = min(payout_data["approved_amount"], effective_cap)
        claim.status = ClaimStatus.APPROVED
        claim.approved_amount = round(approved, 2)
        claim.processed_at = now
        policy.total_claimed = round(weekly_claimed + approved, 2)
        policy.claims_count = (policy.claims_count or 0) + 1

    elif fraud_result["auto_reject"]:
        claim.status = ClaimStatus.REJECTED
        claim.rejection_reason = "; ".join(fraud_result["flags"])
        claim.processed_at = now

    db.add(claim)
    # Commit here to release the lock on the policy row
    await db.commit()
    await db.refresh(claim)

    # Notify on rejection
    if claim.status == ClaimStatus.REJECTED:
        await notify_claim_rejected(db, current_worker, claim)
        await db.commit()

    # Auto-payout if approved and amount > 0
    if claim.status == ClaimStatus.APPROVED and (claim.approved_amount or 0) > 0:
        await notify_claim_approved(db, current_worker, claim, event.disruption_type.value)
        upi_id = current_worker.upi_id or "worker_" + current_worker.id[:8] + "@upi"
        payout_result = await initiate_upi_payout(
            worker_id=current_worker.id,
            upi_id=upi_id,
            amount=claim.approved_amount,
            claim_id=claim.id,
            phone=current_worker.phone,
            disruption_type=event.disruption_type.value,
            bank_account=current_worker.bank_account or "",
            bank_ifsc=current_worker.bank_ifsc or "",
            trigger_time=event_started_at,
        )
        channel = payout_result.get("channel", "UPI")
        settlement_secs = payout_result.get("settlement_seconds", 0)
        payout = Payout(
            claim_id=claim.id,
            worker_id=current_worker.id,
            amount=claim.approved_amount,
            upi_id=upi_id,
            status=PayoutStatus.COMPLETED if payout_result["success"] else (
                PayoutStatus.ROLLED_BACK if payout_result.get("rollback") else PayoutStatus.FAILED
            ),
            razorpay_payout_id=payout_result.get("payout_id"),
            transaction_ref=payout_result.get("transaction_ref"),
            completed_at=now if payout_result["success"] else None,
            channel=channel,
            settlement_seconds=settlement_secs,
            reconciled=payout_result["success"],
        )
        if payout_result["success"]:
            claim.status = ClaimStatus.PAID
            await notify_claim_paid(db, current_worker, claim, upi_id, payout_result.get("transaction_ref", ""))
        elif payout_result.get("rollback"):
            # Rollback: revert policy total_claimed so worker can retry
            policy.total_claimed = round(max(0.0, float(policy.total_claimed or 0) - (claim.approved_amount or 0)), 2)
            policy.claims_count = max(0, (policy.claims_count or 1) - 1)
        db.add(payout)
        await db.commit()
        await db.refresh(claim)

    return claim


@router.get("/", response_model=list[ClaimResponse])
async def list_claims(
    db: AsyncSession = Depends(get_db),
    current_worker: Worker = Depends(get_current_worker),
):
    result = await db.execute(
        select(Claim)
        .where(Claim.worker_id == current_worker.id)
        .order_by(Claim.created_at.desc())
    )
    return result.scalars().all()
