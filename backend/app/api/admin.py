from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text, select, func, and_
from datetime import datetime, timedelta, timezone
from app.database import get_db
from app.models.models import Worker, Policy, Claim, DisruptionEvent, Payout, PolicyStatus, ClaimStatus, PolicyTier

router = APIRouter()


@router.delete("/clear-test-data")
async def clear_test_data(db: AsyncSession = Depends(get_db)):
    """Clear all test data — resets DB for fresh demo."""
    await db.execute(text("TRUNCATE TABLE payouts, claims, policies, disruption_events, workers CASCADE"))
    await db.commit()
    return {"message": "All test data cleared. DB is fresh for demo."}


@router.get("/stats")
async def get_admin_stats(db: AsyncSession = Depends(get_db)):
    """Get overview statistics for the admin dashboard."""
    now = datetime.now(timezone.utc)
    week_ago = now - timedelta(days=7)

    # 1. Basic Metrics
    active_workers_count = await db.execute(select(func.count(Worker.id)).where(Worker.is_active == True))
    active_policies_count = await db.execute(select(func.count(Policy.id)).where(Policy.status == PolicyStatus.ACTIVE))
    claims_this_week_count = await db.execute(select(func.count(Claim.id)).where(Claim.created_at >= week_ago))
    payouts_this_week_sum = await db.execute(select(func.sum(Payout.amount)).where(Payout.initiated_at >= week_ago))

    # 2. Weekly Claims/Payouts Chart (last 7 days)
    weekly_chart = []
    for i in range(7):
        day = (now - timedelta(days=6-i)).date()
        day_start = datetime.combine(day, datetime.min.time(), tzinfo=timezone.utc)
        day_end = datetime.combine(day, datetime.max.time(), tzinfo=timezone.utc)
        
        c_count = await db.execute(select(func.count(Claim.id)).where(and_(Claim.created_at >= day_start, Claim.created_at <= day_end)))
        p_sum = await db.execute(select(func.sum(Payout.amount)).where(and_(Payout.initiated_at >= day_start, Payout.initiated_at <= day_end)))
        
        weekly_chart.append({
            "day": day.strftime("%a"),
            "claims": c_count.scalar() or 0,
            "payouts": float(p_sum.scalar() or 0)
        })

    # 3. Policy Tier Distribution
    tier_dist = []
    for tier in PolicyTier:
        count = await db.execute(select(func.count(Policy.id)).where(Policy.tier == tier))
        tier_dist.append({"name": tier.value.capitalize(), "value": count.scalar() or 0})

    # 4. Fraud Summary
    auto_approved = await db.execute(select(func.count(Claim.id)).where(Claim.auto_approved == True))
    auto_rejected = await db.execute(select(func.count(Claim.id)).where(Claim.status == ClaimStatus.REJECTED))
    under_review = await db.execute(select(func.count(Claim.id)).where(and_(Claim.auto_approved == False, Claim.status == ClaimStatus.PENDING)))

    # 5. Active Disruptions
    active_disruptions = await db.execute(select(DisruptionEvent).where(DisruptionEvent.is_active == True))
    disruptions_list = []
    for d in active_disruptions.scalars():
        disruptions_list.append({
            "city": d.city,
            "type": d.disruption_type.value.replace("_", " ").capitalize(),
            "severity": d.severity.value,
            "dss": d.dss_multiplier,
            "active": d.is_active
        })

    return {
        "metrics": {
            "active_workers": active_workers_count.scalar() or 0,
            "active_policies": active_policies_count.scalar() or 0,
            "claims_this_week": claims_this_week_count.scalar() or 0,
            "payouts_this_week": float(payouts_this_week_sum.scalar() or 0),
        },
        "weekly_chart": weekly_chart,
        "tier_distribution": tier_dist,
        "fraud_summary": {
            "auto_approved": auto_approved.scalar() or 0,
            "under_review": under_review.scalar() or 0,
            "auto_rejected": auto_rejected.scalar() or 0,
        },
        "active_disruptions": disruptions_list
    }


@router.get("/claims")
async def list_all_claims(db: AsyncSession = Depends(get_db)):
    """List all claims for admin."""
    result = await db.execute(
        select(Claim, Worker, DisruptionEvent)
        .join(Worker, Claim.worker_id == Worker.id)
        .join(DisruptionEvent, Claim.disruption_event_id == DisruptionEvent.id)
        .order_by(Claim.created_at.desc())
        .limit(100)
    )
    claims = []
    for row in result.all():
        c, w, e = row
        claims.append({
            "id": c.id[:8].upper(),
            "worker": w.name,
            "city": w.city,
            "event": f"{e.disruption_type.value.replace('_', ' ').capitalize()}",
            "amount": f"₹{c.claimed_amount}",
            "fraud": int(c.fraud_score * 100),
            "status": c.status.value
        })
    return claims


@router.get("/workers")
async def list_all_workers(db: AsyncSession = Depends(get_db)):
    """List all workers for admin."""
    result = await db.execute(select(Worker).order_by(Worker.created_at.desc()).limit(100))
    workers = []
    for w in result.scalars():
        workers.append({
            "id": w.id,
            "name": w.name,
            "phone": w.phone,
            "platform": w.platform.value,
            "city": w.city,
            "risk_score": w.risk_score,
            "is_active": w.is_active,
            "is_verified": w.is_verified
        })
    return workers


@router.get("/disruptions")
async def list_all_disruptions(db: AsyncSession = Depends(get_db)):
    """List all disruptions for admin."""
    result = await db.execute(select(DisruptionEvent).order_by(DisruptionEvent.created_at.desc()).limit(100))
    disruptions = []
    for d in result.scalars():
        disruptions.append({
            "city": d.city,
            "type": d.disruption_type.value.replace("_", " ").capitalize(),
            "severity": d.severity.value,
            "dss": d.dss_multiplier,
            "active": d.is_active,
            "started_at": d.started_at.isoformat() if d.started_at else None
        })
    return disruptions
