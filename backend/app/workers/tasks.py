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

# Lazily populated at first poll via PositionStack geocoding — zero hardcoding.
_supported_cities_cache: list[tuple[str, str]] | None = None


async def _get_supported_cities() -> list[tuple[str, str]]:
    """
    Resolves every city in CITY_ECONOMICS to its pincode via PositionStack.
    Result is cached in-process so geocoding only runs once per worker boot.
    Any city added to CITY_ECONOMICS is automatically included.
    """
    global _supported_cities_cache
    if _supported_cities_cache is not None:
        return _supported_cities_cache

    from app.services.platform_service import CITY_ECONOMICS
    from app.services.geocoding_service import resolve_all_cities

    city_names = list(CITY_ECONOMICS.keys())
    resolved = await resolve_all_cities(city_names)
    _supported_cities_cache = [
        (city, pincode)
        for city, (pincode, _lat, _lng) in resolved.items()
        if pincode != "000000"
    ]
    print(f"[Tasks] Resolved {len(_supported_cities_cache)}/{len(city_names)} cities via PositionStack")
    return _supported_cities_cache


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
    supported = await _get_supported_cities()
    async with AsyncSessionLocal() as db:
        total_events = 0
        total_claims = 0
        for city, pincode in supported:
            event_ids = await _poll_and_store_disruptions(city, pincode, db)
            for eid in event_ids:
                n = await _auto_claim_for_event(eid, city, db)
                total_claims += n
            total_events += len(event_ids)
        return {"cities": len(supported), "new_events": total_events, "auto_claims": total_claims}


async def _do_poll_aqi():
    """Poll AQI for all cities — AQI disruptions are already included in check_disruptions."""
    from app.database import AsyncSessionLocal
    from app.services.disruption_service import fetch_aqi_mock, classify_aqi, get_dss
    from app.models.models import DisruptionEvent, DisruptionType
    from sqlalchemy import select

    supported = await _get_supported_cities()
    async with AsyncSessionLocal() as db:
        total_events = 0
        total_claims = 0
        for city, pincode in supported:
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


@celery_app.task(name="app.workers.tasks.daily_batch_settlement")
def daily_batch_settlement():
    """3am IST daily batch — analyses previous 24hrs for all workers and settles claims."""
    result = _run(_do_daily_batch_settlement())
    print(f"[Celery] Daily batch settlement: {result}")
    return result


async def _do_daily_batch_settlement():
    """
    Production batch settlement flow:
    1. Find all disruption events from last 24hrs
    2. For each active worker, check if any disruption hit their GPS ward
    3. Calculate infra-adjusted payout for the day
    4. Auto-approve if fraud score < 30, else hold for review
    5. Initiate UPI payout — worker gets money by 6am
    6. Activate pending policies (bought after yesterday's 3am)
    """
    from app.database import AsyncSessionLocal
    from sqlalchemy import select, func
    from app.models.models import (
        Worker, Policy, Claim, DisruptionEvent, Payout,
        WorkerLocationPing, PolicyStatus, ClaimStatus, PayoutStatus,
    )
    from app.services.premium_service import calculate_payout, MAX_DAILY_PAYOUT, MAX_WEEKLY_PAYOUT
    from app.services.fraud_service import calculate_fraud_score
    from app.services.infra_service import get_infra_adjusted_dss
    from app.services.payout_service import initiate_upi_payout
    from app.services.notification_service import notify_claim_approved, notify_claim_paid

    now = datetime.now(timezone.utc)
    window_start = now - timedelta(hours=24)
    total_claims = 0
    total_payouts = 0

    async with AsyncSessionLocal() as db:

        # Step 1 — Activate pending policies bought since last batch
        pending_result = await db.execute(
            select(Policy).where(
                Policy.status == PolicyStatus.PENDING,
            )
        )
        pending_policies = pending_result.scalars().all()
        for p in pending_policies:
            p.status = PolicyStatus.ACTIVE
            p.start_date = now
            p.end_date = now + timedelta(days=7)
        await db.commit()
        print(f"[Batch] Activated {len(pending_policies)} pending policies")

        # Step 2 — Get all disruption events from last 24hrs
        events_result = await db.execute(
            select(DisruptionEvent).where(
                DisruptionEvent.started_at >= window_start,
            )
        )
        events = events_result.scalars().all()
        if not events:
            print("[Batch] No disruption events in last 24hrs")
            return {"claims": 0, "payouts": 0, "activated_policies": len(pending_policies)}

        # Step 3 — Get all active workers with policies
        workers_result = await db.execute(
            select(Worker).where(Worker.is_active == True)
        )
        workers = workers_result.scalars().all()

        for worker in workers:
            # Get worker's active policy
            policy_result = await db.execute(
                select(Policy).where(
                    Policy.worker_id == worker.id,
                    Policy.status == PolicyStatus.ACTIVE,
                    Policy.end_date >= now,
                ).order_by(Policy.created_at.desc())
            )
            policy = policy_result.scalars().first()
            if not policy:
                continue

            # Get worker's GPS pings from last 24hrs
            pings_result = await db.execute(
                select(WorkerLocationPing).where(
                    WorkerLocationPing.worker_id == worker.id,
                    WorkerLocationPing.recorded_at >= window_start,
                ).order_by(WorkerLocationPing.recorded_at.asc())
            )
            pings = pings_result.scalars().all()

            # Find disruptions that affected this worker's wards
            for event in events:
                # Match event city to worker's registered city or GPS city
                worker_cities = {worker.city.lower()}
                if pings:
                    worker_cities.update(
                        p.city_detected.lower() for p in pings
                        if p.city_detected
                    )
                if event.city.lower() not in worker_cities:
                    continue

                # Skip if already claimed
                dup = await db.execute(
                    select(Claim).where(
                        Claim.worker_id == worker.id,
                        Claim.disruption_event_id == event.id,
                    )
                )
                if dup.scalar_one_or_none():
                    continue

                # Worker activity zone infra score — weighted average of all
                # wards the worker regularly operates in (last 30 days)
                # More fraud-resistant than real-time pings
                from app.services.infra_service import get_activity_zone_infra_score
                activity_infra = await get_activity_zone_infra_score(
                    worker_id=worker.id,
                    db=db,
                    fallback_city=worker.city,
                    fallback_pincode=worker.pincode,
                    days=30,
                )

                adjusted_dss, infra_hours_ratio, infra_score = await get_infra_adjusted_dss(
                    base_dss=event.dss_multiplier,
                    city=worker.city,
                    pincode=worker.pincode,
                    disruption_type=event.disruption_type.value,
                    severity=event.severity.value,
                    activity_zone_infra=activity_infra,
                )
                adjusted_dss = round(min(
                    event.dss_multiplier * (0.85 + (activity_infra - 0.30) * (0.55 / 0.70)), 1.0
                ), 3)

                # How many active hours did the worker have during the disruption
                event_ist_hour = (event.started_at.hour + 5) % 24
                if 6 <= event_ist_hour < 22:
                    remaining = 22 - event_ist_hour
                    hours_ratio = round(remaining / 16.0, 2)
                else:
                    hours_ratio = 0.5

                effective_hours_ratio = round(
                    min(hours_ratio, infra_hours_ratio), 3
                )

                # Cap checks
                weekly_cap = MAX_WEEKLY_PAYOUT[policy.tier]
                weekly_claimed = float(policy.total_claimed or 0)
                weekly_remaining = max(0.0, weekly_cap - weekly_claimed)
                if weekly_remaining <= 0:
                    continue

                today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
                today_result = await db.execute(
                    select(func.coalesce(func.sum(Claim.approved_amount), 0.0)).where(
                        Claim.worker_id == worker.id,
                        Claim.status.in_([ClaimStatus.APPROVED, ClaimStatus.PAID]),
                        Claim.created_at >= today_start,
                    )
                )
                claimed_today = float(today_result.scalar() or 0)
                daily_remaining = max(0.0, MAX_DAILY_PAYOUT[policy.tier] - claimed_today)
                effective_cap = min(daily_remaining, weekly_remaining)
                if effective_cap <= 0:
                    continue

                # Fraud scoring
                week_ago = now - timedelta(days=7)
                count_result = await db.execute(
                    select(func.count(Claim.id)).where(
                        Claim.worker_id == worker.id,
                        Claim.created_at >= week_ago,
                    )
                )
                claims_this_week = count_result.scalar() or 0

                had_suspicious = any(p.is_suspicious for p in pings)
                latest_ping = pings[-1] if pings else None
                last_known_city = latest_ping.city_detected if latest_ping else ""

                fraud_result = calculate_fraud_score(
                    worker_city=worker.city,
                    event_city=event.city,
                    worker_pincode=worker.pincode,
                    event_pincode=event.pincode or "",
                    was_platform_active=len(pings) > 0,
                    claims_this_week=claims_this_week,
                    claims_same_event=0,
                    event_started_at=event.started_at,
                    claim_created_at=now,
                    disruption_type=event.disruption_type,
                    last_known_city=last_known_city,
                    had_suspicious_ping=had_suspicious,
                    active_hours_ratio=effective_hours_ratio,
                    claim_amount_ratio=1.0,
                    worker_avg_claims_per_week=0.0,
                    zone_avg_claims_per_event=0.0,
                    zone_claim_count_this_event=0,
                    zone_total_workers=0,
                )

                payout_data = calculate_payout(
                    worker_daily_avg=worker.avg_daily_earnings,
                    dss_multiplier=adjusted_dss,
                    active_hours_ratio=effective_hours_ratio,
                    tier=policy.tier,
                    existing_claimed_today=claimed_today,
                )

                claim = Claim(
                    worker_id=worker.id,
                    policy_id=policy.id,
                    disruption_event_id=event.id,
                    status=ClaimStatus.PENDING,
                    claimed_amount=payout_data["raw_payout"],
                    worker_daily_avg=worker.avg_daily_earnings,
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
                await db.flush()
                total_claims += 1

                # UPI payout for approved claims
                if claim.status == ClaimStatus.APPROVED and (claim.approved_amount or 0) > 0:
                    await notify_claim_approved(db, worker, claim, event.disruption_type.value)
                    upi_id = worker.upi_id or "worker_" + worker.id[:8] + "@upi"
                    payout_result = await initiate_upi_payout(
                        worker_id=worker.id,
                        upi_id=upi_id,
                        amount=claim.approved_amount,
                        claim_id=claim.id,
                        phone=worker.phone,
                        disruption_type=event.disruption_type.value,
                        bank_account=worker.bank_account or "",
                        bank_ifsc=worker.bank_ifsc or "",
                        trigger_time=event.started_at,
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
                        channel=payout_result.get("channel", "UPI"),
                        reconciled=payout_result["success"],
                    )
                    if payout_result["success"]:
                        claim.status = ClaimStatus.PAID
                        await notify_claim_paid(db, worker, claim, upi_id,
                                               payout_result.get("transaction_ref", ""))
                        total_payouts += 1
                    db.add(payout)

        await db.commit()

    print(f"[Batch] Done — {total_claims} claims, {total_payouts} payouts")
    return {
        "claims_processed": total_claims,
        "payouts_initiated": total_payouts,
        "activated_policies": len(pending_policies),
        "window": f"{window_start.isoformat()} to {now.isoformat()}",
    }


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
    valid_cities = {c for c, _ in (_run(_get_supported_cities()))}
    if city not in valid_cities:
        return {"error": "Invalid city"}

    async def _run_claims():
        from app.database import AsyncSessionLocal
        async with AsyncSessionLocal() as db:
            return await _auto_claim_for_event(disruption_event_id, city, db)

    n = _run(_run_claims())
    print(f"[Celery] Auto-claims for {disruption_event_id}: {n} claims processed")
    return {"event_id": disruption_event_id, "claims_processed": n}
