"""
Celery tasks — Phase 2: Fully implemented automated triggers
- poll_weather_all_cities: every 15 min → creates DisruptionEvents → auto-claims
- poll_aqi_all_cities: every 60 min → AQI disruption events → auto-claims
- expire_old_policies: daily
- process_auto_claims: triggered per disruption event
"""
import asyncio
import json
from datetime import datetime, timezone, timedelta
from app.workers.celery_app import celery_app

SUPPORTED_CITIES = [
    ("Bangalore", "560001"),
    ("Mumbai", "400001"),
    ("Delhi", "110001"),
    ("Chennai", "600001"),
    ("Hyderabad", "500001"),
]


def _run(coro):
    """Run an async coroutine from a sync Celery task."""
    return asyncio.run(coro)


async def _poll_and_store_disruptions(city: str, pincode: str, db) -> list:
    """Check disruptions for a city, persist new events, return created event IDs."""
    from sqlalchemy import select
    from app.models.models import DisruptionEvent
    from app.services.disruption_service import check_disruptions

    events_data = await check_disruptions(city=city, pincode=pincode)
    created_ids = []

    for e in events_data:
        # Deduplicate: skip if same type+city is already active within last 30 min
        cutoff = datetime.now(timezone.utc) - timedelta(minutes=30)
        dup = await db.execute(
            select(DisruptionEvent).where(
                DisruptionEvent.city == city,
                DisruptionEvent.disruption_type == e["disruption_type"],
                DisruptionEvent.is_active == True,
                DisruptionEvent.started_at >= cutoff,
            )
        )
        if dup.scalar_one_or_none():
            continue

        event = DisruptionEvent(
            disruption_type=e["disruption_type"],
            severity=e["severity"],
            city=city,
            pincode=pincode,
            dss_multiplier=e["dss_multiplier"],
            raw_value=e.get("raw_value"),
            description=e.get("description"),
            source=e.get("source"),
            started_at=datetime.now(timezone.utc),
            is_active=True,
        )
        db.add(event)
        await db.flush()
        created_ids.append(event.id)

    await db.commit()
    return created_ids


async def _auto_claim_for_event(event_id: str, city: str, db):
    """
    For a disruption event, find all workers in that city with an active policy
    and auto-trigger a claim for each (zero-touch claim process).
    """
    from sqlalchemy import select, func
    from datetime import timedelta
    from app.models.models import (
        Worker, Policy, Claim, DisruptionEvent, Payout,
        PolicyStatus, ClaimStatus, PayoutStatus,
    )
    from app.services.premium_service import calculate_payout, MAX_DAILY_PAYOUT, MAX_WEEKLY_PAYOUT
    from app.services.fraud_service import calculate_fraud_score
    from app.services.payout_service import initiate_upi_payout

    now = datetime.now(timezone.utc)

    event_result = await db.execute(
        select(DisruptionEvent).where(DisruptionEvent.id == event_id)
    )
    event = event_result.scalar_one_or_none()
    if not event:
        return 0

    # Find all active policies in this city
    policies_result = await db.execute(
        select(Policy).where(
            Policy.city == city,
            Policy.status == PolicyStatus.ACTIVE,
            Policy.end_date >= now,
        )
    )
    policies = policies_result.scalars().all()

    claimed_count = 0
    for policy in policies:
        worker_result = await db.execute(
            select(Worker).where(Worker.id == policy.worker_id)
        )
        worker = worker_result.scalar_one_or_none()
        if not worker:
            continue

        # Skip if already claimed this event
        dup = await db.execute(
            select(Claim).where(
                Claim.worker_id == worker.id,
                Claim.disruption_event_id == event_id,
            )
        )
        if dup.scalar_one_or_none():
            continue

        # Weekly cap check
        weekly_cap = MAX_WEEKLY_PAYOUT[policy.tier]
        weekly_claimed = float(policy.total_claimed or 0)
        weekly_remaining = max(0.0, weekly_cap - weekly_claimed)
        if weekly_remaining <= 0:
            continue

        # Daily cap check
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        today_result = await db.execute(
            select(func.coalesce(func.sum(Claim.approved_amount), 0.0)).where(
                Claim.worker_id == worker.id,
                Claim.status.in_([ClaimStatus.APPROVED, ClaimStatus.PAID]),
                Claim.created_at >= today_start,
            )
        )
        claimed_today = float(today_result.scalar() or 0)
        daily_cap = MAX_DAILY_PAYOUT[policy.tier]
        daily_remaining = max(0.0, daily_cap - claimed_today)
        effective_cap = min(daily_remaining, weekly_remaining)
        if effective_cap <= 0:
            continue

        # Claims this week for fraud scoring
        week_ago = now - timedelta(days=7)
        count_result = await db.execute(
            select(func.count(Claim.id)).where(
                Claim.worker_id == worker.id,
                Claim.created_at >= week_ago,
            )
        )
        claims_this_week = count_result.scalar() or 0

        fraud_result = calculate_fraud_score(
            worker_city=worker.city,
            event_city=event.city,
            worker_pincode=worker.pincode,
            event_pincode=event.pincode or "",
            was_platform_active=True,  # auto-triggered = worker was active
            claims_this_week=claims_this_week,
            claims_same_event=0,
            event_started_at=event.started_at,
            claim_created_at=now,
        )

        payout_data = calculate_payout(
            worker_daily_avg=worker.avg_daily_earnings,
            dss_multiplier=event.dss_multiplier,
            active_hours_ratio=1.0,
            tier=policy.tier,
            existing_claimed_today=daily_cap - effective_cap,
        )

        claim = Claim(
            worker_id=worker.id,
            policy_id=policy.id,
            disruption_event_id=event.id,
            status=ClaimStatus.PENDING,
            claimed_amount=payout_data["raw_payout"],
            worker_daily_avg=worker.avg_daily_earnings,
            dss_multiplier=event.dss_multiplier,
            active_hours_ratio=1.0,
            fraud_score=fraud_result["fraud_score"],
            fraud_flags=fraud_result["flags_json"],
            auto_approved=fraud_result["auto_approve"],
        )

        if fraud_result["auto_approve"]:
            approved = min(payout_data["income_shortfall"], effective_cap)
            claim.status = ClaimStatus.APPROVED
            claim.approved_amount = round(approved, 2)
            claim.processed_at = now
            policy.total_claimed = round(weekly_claimed + approved, 2)
            policy.claims_count += 1
        elif fraud_result["auto_reject"]:
            claim.status = ClaimStatus.REJECTED
            claim.rejection_reason = "; ".join(fraud_result["flags"])
            claim.processed_at = now

        db.add(claim)
        await db.flush()

        # Initiate UPI payout immediately for approved claims
        if claim.status == ClaimStatus.APPROVED and (claim.approved_amount or 0) > 0:
            upi_id = worker.upi_id or "worker_" + worker.id[:8] + "@upi"
            payout_result = await initiate_upi_payout(
                worker_id=worker.id,
                upi_id=upi_id,
                amount=claim.approved_amount,
                claim_id=claim.id,
                phone=worker.phone,
                disruption_type=event.disruption_type.value,
            )
            payout = Payout(
                claim_id=claim.id,
                worker_id=worker.id,
                amount=claim.approved_amount,
                upi_id=upi_id,
                status=PayoutStatus.COMPLETED if payout_result["success"] else PayoutStatus.FAILED,
                razorpay_payout_id=payout_result.get("payout_id"),
                transaction_ref=payout_result.get("transaction_ref"),
                completed_at=now if payout_result["success"] else None,
            )
            if payout_result["success"]:
                claim.status = ClaimStatus.PAID
            db.add(payout)

        claimed_count += 1

    await db.commit()
    return claimed_count


async def _do_poll_weather():
    from app.database import AsyncSessionLocal
    async with AsyncSessionLocal() as db:
        total_events = 0
        total_claims = 0
        for city, pincode in SUPPORTED_CITIES:
            event_ids = await _poll_and_store_disruptions(city, pincode, db)
            for eid in event_ids:
                n = await _auto_claim_for_event(eid, city, db)
                total_claims += n
            total_events += len(event_ids)
        return {"cities": len(SUPPORTED_CITIES), "new_events": total_events, "auto_claims": total_claims}


async def _do_poll_aqi():
    """Poll AQI for all cities — AQI disruptions are already included in check_disruptions."""
    from app.database import AsyncSessionLocal
    from app.services.disruption_service import fetch_aqi_mock, classify_aqi, get_dss
    from app.models.models import DisruptionEvent, DisruptionType
    from sqlalchemy import select

    async with AsyncSessionLocal() as db:
        total_events = 0
        total_claims = 0
        for city, pincode in SUPPORTED_CITIES:
            aqi_data = await fetch_aqi_mock(city)
            aqi_result = classify_aqi(aqi_data.get("aqi", 0))
            if not aqi_result:
                continue

            severity, desc = aqi_result
            cutoff = datetime.now(timezone.utc) - timedelta(minutes=60)
            dup = await db.execute(
                select(DisruptionEvent).where(
                    DisruptionEvent.city == city,
                    DisruptionEvent.disruption_type == DisruptionType.AQI_SPIKE,
                    DisruptionEvent.is_active == True,
                    DisruptionEvent.started_at >= cutoff,
                )
            )
            if dup.scalar_one_or_none():
                continue

            event = DisruptionEvent(
                disruption_type=DisruptionType.AQI_SPIKE,
                severity=severity,
                city=city,
                pincode=pincode,
                dss_multiplier=get_dss(DisruptionType.AQI_SPIKE, severity),
                raw_value=float(aqi_data["aqi"]),
                description=desc,
                source="AQI India API",
                started_at=datetime.now(timezone.utc),
                is_active=True,
            )
            db.add(event)
            await db.flush()
            n = await _auto_claim_for_event(event.id, city, db)
            total_claims += n
            total_events += 1

        await db.commit()
        return {"new_aqi_events": total_events, "auto_claims": total_claims}


async def _do_expire_policies():
    from app.database import AsyncSessionLocal
    from sqlalchemy import select, update
    from app.models.models import Policy, PolicyStatus

    now = datetime.now(timezone.utc)
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Policy).where(
                Policy.status == PolicyStatus.ACTIVE,
                Policy.end_date < now,
            )
        )
        expired = result.scalars().all()
        for p in expired:
            p.status = PolicyStatus.EXPIRED
        await db.commit()
        return {"expired": len(expired)}


@celery_app.task(name="app.workers.tasks.poll_weather_all_cities")
def poll_weather_all_cities():
    result = _run(_do_poll_weather())
    print(f"[Celery] Weather poll: {result}")
    return result


@celery_app.task(name="app.workers.tasks.poll_aqi_all_cities")
def poll_aqi_all_cities():
    result = _run(_do_poll_aqi())
    print(f"[Celery] AQI poll: {result}")
    return result


@celery_app.task(name="app.workers.tasks.expire_old_policies")
def expire_old_policies():
    result = _run(_do_expire_policies())
    print(f"[Celery] Policy expiry: {result}")
    return result


@celery_app.task(name="app.workers.tasks.process_auto_claims")
def process_auto_claims(disruption_event_id: str, city: str):
    """Manually trigger auto-claims for a specific disruption event."""
    import re
    if not re.fullmatch(r"[0-9a-f\-]{36}", disruption_event_id or ""):
        return {"error": "Invalid disruption_event_id"}
    if city not in {c for c, _ in SUPPORTED_CITIES}:
        return {"error": "Invalid city"}

    async def _run_claims():
        from app.database import AsyncSessionLocal
        async with AsyncSessionLocal() as db:
            return await _auto_claim_for_event(disruption_event_id, city, db)

    n = _run(_run_claims())
    print(f"[Celery] Auto-claims for {disruption_event_id}: {n} claims processed")
    return {"event_id": disruption_event_id, "claims_processed": n}
