from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text, select, func, and_
from datetime import datetime, timedelta, timezone
from app.database import get_db
from app.models.models import Worker, Policy, Claim, DisruptionEvent, Payout, PolicyStatus, ClaimStatus, PolicyTier
from app.services.actuarial_service import calculate_bcr, stress_test_monsoon, TRIGGER_PROBABILITY
from app.config import settings

router = APIRouter()


async def require_admin(x_admin_api_key: str = Header(default="")):
    if settings.ENVIRONMENT != "production" and not settings.ADMIN_API_KEY:
        return True
    if not settings.ADMIN_API_KEY or x_admin_api_key != settings.ADMIN_API_KEY:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    return True


@router.delete("/clear-test-data")
async def clear_test_data(db: AsyncSession = Depends(get_db), _: bool = Depends(require_admin)):
    if settings.ENVIRONMENT == "production":
        raise HTTPException(status_code=404, detail="Not found")
    await db.execute(text("TRUNCATE TABLE payouts, claims, policies, disruption_events, workers CASCADE"))
    await db.commit()
    return {"message": "All test data cleared."}


@router.get("/stats")
async def get_admin_stats(db: AsyncSession = Depends(get_db), _: bool = Depends(require_admin)):
    now = datetime.now(timezone.utc)
    week_ago = now - timedelta(days=7)

    active_workers_count  = await db.execute(select(func.count(Worker.id)).where(Worker.is_active == True))
    active_policies_count = await db.execute(select(func.count(Policy.id)).where(Policy.status == PolicyStatus.ACTIVE))
    claims_this_week      = await db.execute(select(func.count(Claim.id)).where(Claim.created_at >= week_ago))
    payouts_this_week     = await db.execute(select(func.coalesce(func.sum(Payout.amount), 0.0)).where(Payout.initiated_at >= week_ago))

    # Weekly chart
    weekly_chart = []
    for i in range(7):
        day = (now - timedelta(days=6 - i)).date()
        ds = datetime.combine(day, datetime.min.time(), tzinfo=timezone.utc)
        de = datetime.combine(day, datetime.max.time(), tzinfo=timezone.utc)
        c_count = await db.execute(select(func.count(Claim.id)).where(and_(Claim.created_at >= ds, Claim.created_at <= de)))
        p_sum   = await db.execute(select(func.coalesce(func.sum(Payout.amount), 0.0)).where(and_(Payout.initiated_at >= ds, Payout.initiated_at <= de)))
        weekly_chart.append({"day": day.strftime("%a"), "claims": c_count.scalar() or 0, "payouts": float(p_sum.scalar() or 0)})

    # Tier distribution
    tier_dist = []
    for tier in PolicyTier:
        count = await db.execute(select(func.count(Policy.id)).where(Policy.tier == tier))
        tier_dist.append({"name": tier.value.capitalize(), "value": count.scalar() or 0})

    # Eligibility summary (renamed from fraud)
    auto_approved = await db.execute(select(func.count(Claim.id)).where(Claim.auto_approved == True))
    auto_rejected = await db.execute(select(func.count(Claim.id)).where(Claim.status == ClaimStatus.REJECTED))
    under_review  = await db.execute(select(func.count(Claim.id)).where(and_(Claim.auto_approved == False, Claim.status == ClaimStatus.PENDING)))

    # BCR / Loss ratio — live from DB
    total_paid    = await db.execute(select(func.coalesce(func.sum(Payout.amount), 0.0)).where(Payout.status == "completed"))
    total_premium = await db.execute(select(func.coalesce(func.sum(Policy.weekly_premium), 0.0)))
    bcr_data = calculate_bcr(float(total_paid.scalar()), float(total_premium.scalar()))

    # Active disruptions
    active_disruptions = await db.execute(select(DisruptionEvent).where(DisruptionEvent.is_active == True))
    disruptions_list = [
        {
            "city":     d.city,
            "type":     d.disruption_type.value.replace("_", " ").capitalize(),
            "severity": d.severity.value,
            "dss":      d.dss_multiplier,
            "active":   d.is_active,
        }
        for d in active_disruptions.scalars()
    ]

    return {
        "metrics": {
            "active_workers":    active_workers_count.scalar() or 0,
            "active_policies":   active_policies_count.scalar() or 0,
            "claims_this_week":  claims_this_week.scalar() or 0,
            "payouts_this_week": float(payouts_this_week.scalar() or 0),
        },
        "weekly_chart":       weekly_chart,
        "tier_distribution":  tier_dist,
        "eligibility_summary": {
            "auto_approved": auto_approved.scalar() or 0,
            "under_review":  under_review.scalar() or 0,
            "auto_rejected": auto_rejected.scalar() or 0,
        },
        # backward-compat alias used by dashboard FraudGauge
        "fraud_summary": {
            "auto_approved": auto_approved.scalar() or 0,
            "under_review":  under_review.scalar() or 0,
            "auto_rejected": auto_rejected.scalar() or 0,
        },
        "bcr":                bcr_data,
        "active_disruptions": disruptions_list,
    }


@router.get("/claims")
async def list_all_claims(db: AsyncSession = Depends(get_db), _: bool = Depends(require_admin)):
    result = await db.execute(
        select(Claim, Worker, DisruptionEvent)
        .join(Worker, Claim.worker_id == Worker.id)
        .join(DisruptionEvent, Claim.disruption_event_id == DisruptionEvent.id)
        .order_by(Claim.created_at.desc())
        .limit(100)
    )
    return [
        {
            "id":     c.id[:8].upper(),
            "worker": w.name,
            "city":   w.city,
            "event":  e.disruption_type.value.replace("_", " ").capitalize(),
            "amount": f"₹{c.claimed_amount:.0f}",
            "eligibility_score": int(c.fraud_score) if c.fraud_score else 0,
            "status": c.status.value,
        }
        for c, w, e in result.all()
    ]


@router.get("/workers")
async def list_all_workers(db: AsyncSession = Depends(get_db), _: bool = Depends(require_admin)):
    result = await db.execute(select(Worker).order_by(Worker.created_at.desc()).limit(100))
    return [
        {
            "id":           w.id,
            "name":         w.name,
            "phone":        w.phone,
            "platform":     w.platform.value,
            "city":         w.city,
            "risk_score":   w.risk_score,
            "penalty_score": w.penalty_score or 0.0,
            "is_active":    w.is_active,
            "is_verified":  w.is_verified,
        }
        for w in result.scalars()
    ]


@router.get("/disruptions")
async def list_all_disruptions(db: AsyncSession = Depends(get_db), _: bool = Depends(require_admin)):
    result = await db.execute(select(DisruptionEvent).order_by(DisruptionEvent.created_at.desc()).limit(100))
    return [
        {
            "city":       d.city,
            "type":       d.disruption_type.value.replace("_", " ").capitalize(),
            "severity":   d.severity.value,
            "dss":        d.dss_multiplier,
            "active":     d.is_active,
            "started_at": d.started_at.isoformat() if d.started_at else None,
            "ended_at":   d.ended_at.isoformat() if d.ended_at else None,
        }
        for d in result.scalars()
    ]


@router.get("/analytics")
async def get_analytics(db: AsyncSession = Depends(get_db), _: bool = Depends(require_admin)):
    now = datetime.now(timezone.utc)

    # Loss ratio per city — derived from actual DB data only
    active_cities_result = await db.execute(
        select(Worker.city).join(Policy, Policy.worker_id == Worker.id)
        .where(Policy.status == PolicyStatus.ACTIVE).distinct()
    )
    cities = [r[0] for r in active_cities_result.all()] or ["Bangalore", "Mumbai", "Delhi", "Chennai", "Hyderabad"]

    city_loss = []
    for city in cities:
        city_paid = await db.execute(
            select(func.coalesce(func.sum(Payout.amount), 0.0))
            .join(Claim, Payout.claim_id == Claim.id)
            .join(Worker, Claim.worker_id == Worker.id)
            .where(Worker.city == city, Payout.status == "completed")
        )
        city_premium = await db.execute(
            select(func.coalesce(func.sum(Policy.weekly_premium), 0.0))
            .join(Worker, Policy.worker_id == Worker.id)
            .where(Worker.city == city)
        )
        paid    = float(city_paid.scalar())
        premium = float(city_premium.scalar())
        city_loss.append({
            "city":       city,
            "loss_ratio": round(paid / premium, 3) if premium > 0 else 0.0,
            "paid":       paid,
            "premium":    premium,
        })

    # Next-week forecast from actuarial trigger probabilities
    forecast = []
    for city in cities[:6]:
        probs    = TRIGGER_PROBABILITY.get(city, {})
        top_risk = sorted(probs.items(), key=lambda x: x[1], reverse=True)[:2]
        at_risk_result = await db.execute(
            select(func.count(Policy.id))
            .join(Worker, Policy.worker_id == Worker.id)
            .where(Worker.city == city, Policy.status == PolicyStatus.ACTIVE)
        )
        at_risk = at_risk_result.scalar() or 0
        forecast.append({
            "city":             city,
            "workers_at_risk":  at_risk,
            "top_risks":        [{"peril": p, "probability": round(v * 100, 1)} for p, v in top_risk],
            "estimated_claims": round(at_risk * sum(v for _, v in top_risk), 0),
        })

    # Eligibility (fraud) trend — last 7 days
    eligibility_trend = []
    for i in range(7):
        day = (now - timedelta(days=6 - i)).date()
        ds  = datetime.combine(day, datetime.min.time(), tzinfo=timezone.utc)
        de  = datetime.combine(day, datetime.max.time(), tzinfo=timezone.utc)
        flagged = await db.execute(
            select(func.count(Claim.id)).where(
                and_(Claim.created_at >= ds, Claim.created_at <= de, Claim.fraud_score > 30)
            )
        )
        eligibility_trend.append({"day": day.strftime("%a"), "flagged": flagged.scalar() or 0})

    return {
        "city_loss_ratios":   city_loss,
        "next_week_forecast": forecast,
        "stress_test":        stress_test_monsoon("Mumbai", 650.0, PolicyTier.SMART),
        "eligibility_trend":  eligibility_trend,
    }


@router.get("/claims/{claim_id}/eligibility")
async def get_claim_eligibility_detail(claim_id: str, db: AsyncSession = Depends(get_db), _: bool = Depends(require_admin)):
    import json
    result = await db.execute(
        select(Claim, Worker).join(Worker, Claim.worker_id == Worker.id)
        .where(Claim.id.ilike(f"{claim_id}%"))
    )
    row = result.first()
    if not row:
        raise HTTPException(status_code=404, detail="Claim not found")
    c, w = row
    score = c.fraud_score or 0
    return {
        "claim_id":        c.id,
        "worker":          w.name,
        "eligibility_score": score,
        "verdict":         "APPROVED" if score < 30 else "REVIEW" if score < 70 else "REJECTED",
        "flags":           json.loads(c.fraud_flags or "[]"),
        "auto_approved":   c.auto_approved,
        "status":          c.status.value,
    }


# Backward-compatible alias so existing dashboard calls to /admin/claims/{id}/fraud still work
@router.get("/claims/{claim_id}/fraud")
async def get_claim_fraud_detail_alias(claim_id: str, db: AsyncSession = Depends(get_db), _: bool = Depends(require_admin)):
    return await get_claim_eligibility_detail(claim_id, db, _)


@router.post("/claims/{claim_id}/investigate")
async def investigate_claim_endpoint(
    claim_id: str,
    db: AsyncSession = Depends(get_db),
    _: bool = Depends(require_admin),
):
    """
    Trigger the Agentic AI investigation on a claim.
    Runs 5 evidence steps, produces a verdict + explanation.
    Automatically updates claim status and worker penalty_score.
    """
    import json
    from app.models.models import Claim, Worker, ClaimStatus
    from app.services.agentic_service import investigate_claim
    from app.services.notification_service import notify_claim_approved, notify_claim_rejected

    result_row = await db.execute(
        select(Claim, Worker)
        .join(Worker, Claim.worker_id == Worker.id)
        .where(Claim.id.ilike(f"{claim_id}%"))
    )
    row = result_row.first()
    if not row:
        raise HTTPException(status_code=404, detail="Claim not found")
    claim, worker = row

    # Run the agent
    investigation = await investigate_claim(claim.id, db)
    if "error" in investigation:
        raise HTTPException(status_code=404, detail=investigation["error"])

    # Persist investigation result on claim
    claim.ai_investigation = json.dumps(investigation)
    now = datetime.now(timezone.utc)

    if investigation["verdict"] == "APPROVED":
        claim.status = ClaimStatus.APPROVED
        claim.processed_at = now
        # Calculate payout if not already set
        if not claim.approved_amount:
            claim.approved_amount = round(claim.claimed_amount * 0.8, 2)  # conservative 80%
        # Update policy total_claimed
        from app.models.models import Policy
        policy_result = await db.execute(
            select(Policy).where(Policy.id == claim.policy_id)
        )
        policy = policy_result.scalar_one_or_none()
        if policy:
            policy.total_claimed = round(float(policy.total_claimed or 0) + (claim.approved_amount or 0), 2)
            policy.claims_count = (policy.claims_count or 0) + 1
        from app.models.models import DisruptionEvent
        event_result = await db.execute(
            select(DisruptionEvent).where(DisruptionEvent.id == claim.disruption_event_id)
        )
        event = event_result.scalar_one_or_none()
        if event:
            await notify_claim_approved(db, worker, claim, event.disruption_type.value)
    else:
        claim.status = ClaimStatus.REJECTED
        claim.processed_at = now
        claim.rejection_reason = investigation["explanation"]
        # Apply penalty to worker
        penalty = investigation.get("penalty", 0)
        if penalty > 0:
            worker.penalty_score = round(float(worker.penalty_score or 0) + penalty, 1)
            worker.risk_score = min(1.0, round(float(worker.risk_score or 0.5) + penalty / 100.0, 3))
        await notify_claim_rejected(db, worker, claim)

    await db.commit()
    await db.refresh(claim)
    return {
        "claim_id": claim.id,
        "new_status": claim.status.value,
        "investigation": investigation,
    }


@router.post("/claims/{claim_id}/override")
async def override_claim(
    claim_id: str,
    body: dict,
    db: AsyncSession = Depends(get_db),
    _: bool = Depends(require_admin),
):
    """
    Manual admin override — approve or reject a claim with a reason.
    body: { "action": "approve" | "reject", "reason": str }
    """
    from app.models.models import Claim, Worker, ClaimStatus
    from app.services.notification_service import notify_claim_approved, notify_claim_rejected

    action = body.get("action", "").lower()
    reason = body.get("reason", "Manual admin override")
    if action not in ("approve", "reject"):
        raise HTTPException(status_code=400, detail="action must be 'approve' or 'reject'")

    result_row = await db.execute(
        select(Claim, Worker)
        .join(Worker, Claim.worker_id == Worker.id)
        .where(Claim.id.ilike(f"{claim_id}%"))
    )
    row = result_row.first()
    if not row:
        raise HTTPException(status_code=404, detail="Claim not found")
    claim, worker = row

    now = datetime.now(timezone.utc)
    if action == "approve":
        claim.status = ClaimStatus.APPROVED
        claim.processed_at = now
        if not claim.approved_amount:
            claim.approved_amount = round(claim.claimed_amount * 0.8, 2)
        from app.models.models import Policy, DisruptionEvent
        policy_result = await db.execute(select(Policy).where(Policy.id == claim.policy_id))
        policy = policy_result.scalar_one_or_none()
        if policy:
            policy.total_claimed = round(float(policy.total_claimed or 0) + (claim.approved_amount or 0), 2)
            policy.claims_count = (policy.claims_count or 0) + 1
        event_result = await db.execute(select(DisruptionEvent).where(DisruptionEvent.id == claim.disruption_event_id))
        event = event_result.scalar_one_or_none()
        if event:
            await notify_claim_approved(db, worker, claim, event.disruption_type.value)
    else:
        claim.status = ClaimStatus.REJECTED
        claim.processed_at = now
        claim.rejection_reason = reason
        await notify_claim_rejected(db, worker, claim)

    await db.commit()
    return {"claim_id": claim.id, "new_status": claim.status.value, "reason": reason}


@router.get("/disbursement-ratio")
async def get_disbursement_ratio(db: AsyncSession = Depends(get_db), _: bool = Depends(require_admin)):
    """
    Claim disbursement / premium collection ratio per city and overall.
    Shows BCR health, total premiums collected, total claims paid, and ratio.
    """
    from app.models.models import Worker

    # Overall
    total_paid_result = await db.execute(
        select(func.coalesce(func.sum(Payout.amount), 0.0)).where(Payout.status == "completed")
    )
    total_premium_result = await db.execute(
        select(func.coalesce(func.sum(Policy.weekly_premium), 0.0))
    )
    total_paid = float(total_paid_result.scalar())
    total_premium = float(total_premium_result.scalar())
    overall_ratio = round(total_paid / total_premium, 4) if total_premium > 0 else 0.0

    # Per city
    cities_result = await db.execute(
        select(Worker.city).join(Policy, Policy.worker_id == Worker.id).distinct()
    )
    cities = [r[0] for r in cities_result.all()]

    city_ratios = []
    for city in cities:
        city_paid = await db.execute(
            select(func.coalesce(func.sum(Payout.amount), 0.0))
            .join(Claim, Payout.claim_id == Claim.id)
            .join(Worker, Claim.worker_id == Worker.id)
            .where(Worker.city == city, Payout.status == "completed")
        )
        city_premium = await db.execute(
            select(func.coalesce(func.sum(Policy.weekly_premium), 0.0))
            .join(Worker, Policy.worker_id == Worker.id)
            .where(Worker.city == city)
        )
        paid = float(city_paid.scalar())
        premium = float(city_premium.scalar())
        ratio = round(paid / premium, 4) if premium > 0 else 0.0
        status = "healthy" if 0.55 <= ratio <= 0.70 else ("critical" if ratio > 0.85 else ("elevated" if ratio > 0.70 else "low"))
        city_ratios.append({
            "city": city,
            "premium_collected": premium,
            "claims_disbursed": paid,
            "ratio": ratio,
            "ratio_pct": round(ratio * 100, 1),
            "status": status,
        })

    # Per tier
    tier_ratios = []
    for tier in PolicyTier:
        tier_paid = await db.execute(
            select(func.coalesce(func.sum(Payout.amount), 0.0))
            .join(Claim, Payout.claim_id == Claim.id)
            .join(Policy, Claim.policy_id == Policy.id)
            .where(Policy.tier == tier, Payout.status == "completed")
        )
        tier_premium = await db.execute(
            select(func.coalesce(func.sum(Policy.weekly_premium), 0.0))
            .where(Policy.tier == tier)
        )
        paid = float(tier_paid.scalar())
        premium = float(tier_premium.scalar())
        ratio = round(paid / premium, 4) if premium > 0 else 0.0
        tier_ratios.append({
            "tier": tier.value,
            "premium_collected": premium,
            "claims_disbursed": paid,
            "ratio": ratio,
            "ratio_pct": round(ratio * 100, 1),
        })

    bcr_data = calculate_bcr(total_paid, total_premium)

    return {
        "overall": {
            "premium_collected": total_premium,
            "claims_disbursed": total_paid,
            "ratio": overall_ratio,
            "ratio_pct": round(overall_ratio * 100, 1),
            "bcr_status": bcr_data["status"],
            "bcr_action": bcr_data["action"],
            "target_range": "55%–70%",
        },
        "by_city": city_ratios,
        "by_tier": tier_ratios,
    }


@router.get("/geography-tiers")
async def get_geography_tiers(_: bool = Depends(require_admin)):
    """
    Returns city-specific tier coverage — which disruption types are relevant
    per city and what each tier covers there.
    Used by admin to understand and configure geography-tailored offerings.
    """
    from app.api.claims import CITY_POOLS
    from app.models.models import DisruptionType
    from app.services.actuarial_service import TIER_PERILS, TRIGGER_PROBABILITY, DEFAULT_TRIGGER_PROB
    from app.services.premium_service import BASE_PREMIUMS, MAX_DAILY_PAYOUT, MAX_WEEKLY_PAYOUT

    result = {}
    for city, covered_types in CITY_POOLS.items():
        city_probs = TRIGGER_PROBABILITY.get(city, DEFAULT_TRIGGER_PROB)
        tiers = {}
        for tier in PolicyTier:
            tier_perils = TIER_PERILS[tier]
            # Only show perils that are both in this tier AND relevant for this city
            relevant_perils = [
                p for p in tier_perils
                if any(p in ct.value for ct in covered_types)
            ]
            tiers[tier.value] = {
                "base_premium": BASE_PREMIUMS[tier],
                "max_daily_payout": MAX_DAILY_PAYOUT[tier],
                "max_weekly_payout": MAX_WEEKLY_PAYOUT[tier],
                "relevant_perils": [
                    {
                        "type": p,
                        "annual_trigger_probability_pct": round(city_probs.get(p, 0.05) * 100, 1),
                    }
                    for p in relevant_perils
                ],
                "irrelevant_perils_excluded": [
                    p for p in tier_perils if p not in relevant_perils
                ],
            }
        result[city] = {"tiers": tiers, "covered_disruption_types": [ct.value for ct in covered_types]}

    return result
