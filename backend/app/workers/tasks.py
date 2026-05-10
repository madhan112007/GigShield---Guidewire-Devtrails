"""
Celery tasks — Phase 2: Fully implemented automated triggers
- poll_weather_all_cities: every 15 min → creates DisruptionEvents → auto-claims
- poll_aqi_all_cities: every 60 min → AQI disruption events → auto-claims
- expire_old_policies: daily
- process_auto_claims: triggered per disruption event
"""
import asyncio
import json
import os
import sys
from datetime import datetime, timezone, timedelta
from app.workers.celery_app import celery_app

async def _get_cities_to_poll() -> list[tuple[str, str, float, float]]:
    """
    Dynamically builds the city poll list from the DB — covers every city
    where at least one active worker exists, anywhere in India.
    Returns list of (city, pincode, lat, lng) tuples.
    lat/lng resolved via geocoding_service — used by TomTom traffic API
    so traffic works for any Indian city, not just hardcoded ones.
    """
    from app.database import AsyncSessionLocal
    from sqlalchemy import select
    from app.models.models import Worker, Policy, PolicyStatus
    from app.services.geocoding_service import resolve_city

    async with AsyncSessionLocal() as db:
        rows = await db.execute(
            select(Worker.city, Worker.pincode)
            .join(Policy, Policy.worker_id == Worker.id)
            .where(
                Worker.is_active == True,
                Policy.status == PolicyStatus.ACTIVE,
            )
            .distinct()
        )
        worker_locations = rows.all()

    city_map: dict[str, tuple] = {}
    for city, pincode in worker_locations:
        if not city:
            continue
        city_key = city.strip().lower()
        if city_key not in city_map:
            if pincode and len(pincode.strip()) == 6 and pincode.strip().isdigit():
                resolved_pincode, lat, lng = await resolve_city(city.strip())
                # Use worker's own pincode but geocoded lat/lng
                final_pincode = pincode.strip() if pincode.strip() != "000000" else resolved_pincode
                city_map[city_key] = (city.strip(), final_pincode, lat, lng)
            else:
                resolved_pincode, lat, lng = await resolve_city(city.strip())
                if resolved_pincode != "000000":
                    city_map[city_key] = (city.strip(), resolved_pincode, lat, lng)

    result = list(city_map.values())
    print(f"[Tasks] Polling {len(result)} cities derived from active workers in DB")
    return result


def _run(coro):
    """Run an async coroutine from a sync Celery task."""
    return asyncio.run(coro)


async def _poll_and_store_disruptions(city: str, pincode: str, db, lat: float = 0.0, lng: float = 0.0) -> list:
    """Check disruptions for a city, persist new events, return created event IDs."""
    from sqlalchemy import select
    from app.models.models import DisruptionEvent
    from app.services.disruption_service import (
        check_disruptions, fetch_weather_real, fetch_aqi_real, check_disruption_cleared,
    )

    now = datetime.now(timezone.utc)

    # Close any active events whose sensor readings have returned to normal
    active_result = await db.execute(
        select(DisruptionEvent).where(
            DisruptionEvent.city == city,
            DisruptionEvent.is_active == True,
        )
    )
    active_events = active_result.scalars().all()
    if active_events:
        weather = await fetch_weather_real(city)
        aqi_data = await fetch_aqi_real(city)
        for ev in active_events:
            if check_disruption_cleared(ev.disruption_type, weather, aqi_data):
                ev.is_active = False
                ev.ended_at = now

    events_data = await check_disruptions(city=city, pincode=pincode, lat=lat, lng=lng)
    created_ids = []

    for e in events_data:
        # Deduplicate: skip if same type+city is already active within last 30 min
        cutoff = now - timedelta(minutes=30)
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
            started_at=now,
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
        WorkerLocationPing, PolicyStatus, ClaimStatus, PayoutStatus,
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

        # Check if worker had GPS pings during the disruption window
        # (proxy for platform activity — worker was out delivering)
        ping_window_start = event.started_at - timedelta(hours=1)
        ping_result = await db.execute(
            select(func.count()).select_from(WorkerLocationPing).where(
                WorkerLocationPing.worker_id == worker.id,
                WorkerLocationPing.recorded_at >= ping_window_start,
                WorkerLocationPing.recorded_at <= event.started_at + timedelta(hours=2),
            )
        )
        was_platform_active = (ping_result.scalar() or 0) > 0

        from app.services.infra_service import resolve_worker_adjusted_dss
        try:
            adjusted_dss, adjusted_hours_ratio, _ = await resolve_worker_adjusted_dss(
                event=event,
                worker_id=worker.id,
                worker_city=worker.city,
                worker_pincode=worker.pincode,
                db=db,
            )
        except Exception:
            adjusted_dss = event.dss_multiplier
            adjusted_hours_ratio = 1.0

        fraud_result = calculate_fraud_score(
            worker_city=worker.city,
            event_city=event.city,
            worker_pincode=worker.pincode,
            event_pincode=event.pincode or "",
            was_platform_active=was_platform_active,
            claims_this_week=claims_this_week,
            claims_same_event=0,
            event_started_at=event.started_at,
            claim_created_at=now,
        )

        payout_data = calculate_payout(
            worker_daily_avg=worker.avg_daily_earnings,
            dss_multiplier=adjusted_dss,
            active_hours_ratio=adjusted_hours_ratio,
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
            dss_multiplier=adjusted_dss,
            active_hours_ratio=adjusted_hours_ratio,
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
    cities = await _get_cities_to_poll()
    async with AsyncSessionLocal() as db:
        total_events = 0
        total_claims = 0
        for city, pincode, lat, lng in cities:
            event_ids = await _poll_and_store_disruptions(city, pincode, db, lat=lat, lng=lng)
            for eid in event_ids:
                n = await _auto_claim_for_event(eid, city, db)
                total_claims += n
            total_events += len(event_ids)
        return {"cities": len(cities), "new_events": total_events, "auto_claims": total_claims}


async def _do_poll_aqi():
    """AQI disruptions are handled inside check_disruptions — this task just triggers the full poll."""
    return await _do_poll_weather()


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


@celery_app.task(name="app.workers.tasks.retrain_premium_model")
def retrain_premium_model():
    """
    Weekly auto-retrain of the premium engine — runs every Sunday 3:30am IST.
    Blends real claims from DB with synthetic data + real weather risk factors.
    Model improves automatically as real claims accumulate.
    """
    try:
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../"))
        from ml.premium_engine.train import run_auto_retrain
        metrics = run_auto_retrain()
        print(f"[Celery] Premium model retrained — MAE=₹{metrics['mae']:.2f} "
              f"R²={metrics['r2']:.4f} "
              f"real_claims={metrics['real_claims_rows']}")
        return metrics
    except Exception as e:
        print(f"[Celery] Premium retrain FAILED: {e}")
        return {"error": str(e)}


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
    2. For each active worker, check if any disruption hit their delivery zone
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
    from app.services.payout_service import initiate_upi_payout
    from app.services.notification_service import notify_claim_approved, notify_claim_paid
    from app.api.claims import active_hours_ratio

    now = datetime.now(timezone.utc)
    window_start = now - timedelta(hours=24)
    total_claims = 0
    total_payouts = 0

    async with AsyncSessionLocal() as db:

        # Step 1 — Activate pending policies bought since last batch
        # Guard: only activate policies created within the last 48hrs to avoid
        # activating stale zombie pending policies from failed payments.
        pending_cutoff = now - timedelta(hours=48)
        pending_result = await db.execute(
            select(Policy).where(
                Policy.status == PolicyStatus.PENDING,
                Policy.created_at >= pending_cutoff,
            )
        )
        pending_policies = pending_result.scalars().all()
        for p in pending_policies:
            # Idempotency: only set dates if not already set (handles double-fire)
            if p.start_date is None:
                p.start_date = now
                p.end_date = now + timedelta(days=7)
            p.status = PolicyStatus.ACTIVE
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

        # Bulk-fetch all GPS pings for active workers in last 24hrs (avoids N+1)
        worker_ids = [w.id for w in workers]
        all_pings_result = await db.execute(
            select(WorkerLocationPing).where(
                WorkerLocationPing.worker_id.in_(worker_ids),
                WorkerLocationPing.recorded_at >= window_start,
            ).order_by(WorkerLocationPing.recorded_at.asc())
        )
        all_pings = all_pings_result.scalars().all()
        pings_by_worker: dict[str, list] = {wid: [] for wid in worker_ids}
        for ping in all_pings:
            pings_by_worker[ping.worker_id].append(ping)

        # Bulk-fetch today's claimed amounts per worker (avoids N+1)
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        daily_sums_result = await db.execute(
            select(Claim.worker_id, func.coalesce(func.sum(Claim.approved_amount), 0.0)).where(
                Claim.worker_id.in_(worker_ids),
                Claim.status.in_([ClaimStatus.APPROVED, ClaimStatus.PAID]),
                Claim.created_at >= today_start,
            ).group_by(Claim.worker_id)
        )
        claimed_today_by_worker: dict[str, float] = {row[0]: float(row[1]) for row in daily_sums_result.all()}

        # Bulk-fetch weekly claim counts per worker (avoids N+1)
        week_ago = now - timedelta(days=7)
        weekly_counts_result = await db.execute(
            select(Claim.worker_id, func.count(Claim.id)).where(
                Claim.worker_id.in_(worker_ids),
                Claim.created_at >= week_ago,
            ).group_by(Claim.worker_id)
        )
        weekly_counts_by_worker: dict[str, int] = {row[0]: int(row[1]) for row in weekly_counts_result.all()}

        # Bulk-fetch 12-week claim history for worker_history_factor (avoids N+1)
        twelve_weeks_ago = now - timedelta(weeks=12)
        history_counts_result = await db.execute(
            select(Claim.worker_id, func.count(Claim.id)).where(
                Claim.worker_id.in_(worker_ids),
                Claim.created_at >= twelve_weeks_ago,
                Claim.status.in_([ClaimStatus.APPROVED, ClaimStatus.PAID]),
            ).group_by(Claim.worker_id)
        )
        history_counts_by_worker: dict[str, int] = {row[0]: int(row[1]) for row in history_counts_result.all()}

        for worker in workers:
          try:
            # Skip workers scheduled for purge — avoid race with purge_deleted_accounts
            if worker.is_deleted:
                continue

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

            # Get worker's GPS pings from last 24hrs (pre-fetched)
            pings = pings_by_worker.get(worker.id, [])

            # Find disruptions that affected this worker's delivery zones
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

                from app.services.infra_service import resolve_worker_adjusted_dss
                try:
                    adjusted_dss, infra_hours_ratio, activity_infra = await resolve_worker_adjusted_dss(
                        event=event,
                        worker_id=worker.id,
                        worker_city=worker.city,
                        worker_pincode=worker.pincode,
                        db=db,
                    )
                except Exception as e:
                    print(f"[Batch] resolve_worker_adjusted_dss fallback for worker {worker.id[:8]}: {e}")
                    adjusted_dss = event.dss_multiplier
                    infra_hours_ratio = active_hours_ratio(event)
                    activity_infra = 0.65

                # Actual hours lost: ended_at - started_at clamped to 6am-10pm IST
                effective_hours_ratio = active_hours_ratio(event)

                # Cap checks
                weekly_cap = MAX_WEEKLY_PAYOUT[policy.tier]
                weekly_claimed = float(policy.total_claimed or 0)
                weekly_remaining = max(0.0, weekly_cap - weekly_claimed)
                if weekly_remaining <= 0:
                    continue

                claimed_today = claimed_today_by_worker.get(worker.id, 0.0)
                daily_remaining = max(0.0, MAX_DAILY_PAYOUT[policy.tier] - claimed_today)
                effective_cap = min(daily_remaining, weekly_remaining)
                if effective_cap <= 0:
                    continue

                claims_this_week = weekly_counts_by_worker.get(worker.id, 0)

                # ── worker_history_factor from real 12-week claim history ────
                # High claimers pay more on renewal; low claimers get discount.
                # Clamped to [0.85, 1.30] to prevent extreme swings.
                EXPECTED_CLAIMS_12W = 6.0
                actual_claims_12w = history_counts_by_worker.get(worker.id, 0)
                if actual_claims_12w == 0:
                    worker_history_factor = 0.90  # no claims = lower risk
                else:
                    worker_history_factor = round(
                        max(0.85, min(1.30, actual_claims_12w / EXPECTED_CLAIMS_12W)), 3
                    )

                # ── Platform activity check (mock API) ───────────────────────
                # Confirms worker was actually online on their delivery platform
                # during the disruption window — not just GPS-present.
                # Fallback: if API fails, assume active (activity_ratio=1.0)
                # so a platform API outage never blocks legitimate payouts.
                from app.services.platform_service import fetch_platform_activity
                try:
                    platform_activity = await fetch_platform_activity(
                        phone=worker.phone,
                        platform=worker.platform.value if worker.platform else "zomato",
                        window_start=event.started_at,
                        window_end=event.ended_at or now,
                    )
                    platform_ratio = platform_activity["activity_ratio"]
                    was_platform_active = platform_activity["was_active"]
                except Exception as e:
                    print(f"[Batch] platform_activity fallback for worker {worker.id[:8]}: {e}")
                    platform_ratio = 1.0
                    was_platform_active = True

                # If worker was completely offline on platform during disruption,
                # skip claim — they weren't losing income.
                if not was_platform_active:
                    print(f"[Batch] Worker {worker.id[:8]} skipped — platform inactive during {event.disruption_type.value}")
                    continue

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
                    active_hours_ratio=round(effective_hours_ratio * platform_ratio, 3),
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
                        status=PayoutStatus.COMPLETED if payout_result["success"] else (
                            PayoutStatus.ROLLED_BACK if payout_result.get("rollback") else PayoutStatus.FAILED
                        ),
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
                    else:
                        # Payout failed — claim stays APPROVED so it can be retried
                        print(f"[Batch] Payout FAILED for claim {claim.id} worker {worker.id}: {payout_result.get('error', 'unknown')}")
                    db.add(payout)

          except Exception as e:
              print(f"[Batch] ERROR processing worker {worker.id}: {e}")
              await db.rollback()
              continue

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


@celery_app.task(name="app.workers.tasks.purge_deleted_accounts")
def purge_deleted_accounts():
    """Daily job: permanently purge worker rows whose 30-day grace period has ended."""
    result = _run(_do_purge_deleted_accounts())
    print(f"[Celery] Purge deleted accounts: {result}")
    return result


async def _do_purge_deleted_accounts():
    """
    Permanently purge anonymised worker rows after 30-day grace period.
    Financial records (claims, policies, payouts) are kept — they reference
    worker_id (UUID) which is now fully detached from any PII.
    """
    from app.database import AsyncSessionLocal
    from sqlalchemy import select
    from app.models.models import Worker, DeletedAccountArchive

    now = datetime.now(timezone.utc)
    purged = 0

    async with AsyncSessionLocal() as db:
        # Find workers past grace period
        result = await db.execute(
            select(Worker).where(
                Worker.is_deleted == True,
                Worker.deletion_requested_at <= now - timedelta(days=30),
            )
        )
        workers = result.scalars().all()

        for worker in workers:
            # Mark archive as purged
            archive_result = await db.execute(
                select(DeletedAccountArchive).where(
                    DeletedAccountArchive.original_worker_id == worker.id,
                    DeletedAccountArchive.permanently_purged_at.is_(None),
                )
            )
            archive = archive_result.scalar_one_or_none()
            if archive:
                archive.permanently_purged_at = now

            # Hard delete the anonymised worker row
            # Claims/policies/payouts remain — they are pseudonymised (UUID only)
            await db.delete(worker)
            purged += 1

        await db.commit()

    return {"purged": purged}


@celery_app.task(name="app.workers.tasks.process_auto_claims")
def process_auto_claims(disruption_event_id: str, city: str):
    """Manually trigger auto-claims for a specific disruption event."""
    import re
    if not re.fullmatch(r"[0-9a-f\-]{36}", disruption_event_id or ""):
        return {"error": "Invalid disruption_event_id"}
    valid_cities = {c for c, _, _, _ in (_run(_get_cities_to_poll()))}
    if city not in valid_cities:
        return {"error": "Invalid city"}

    async def _run_claims():
        from app.database import AsyncSessionLocal
        async with AsyncSessionLocal() as db:
            return await _auto_claim_for_event(disruption_event_id, city, db)

    n = _run(_run_claims())
    print(f"[Celery] Auto-claims for {disruption_event_id}: {n} claims processed")
    return {"event_id": disruption_event_id, "claims_processed": n}


@celery_app.task(name="app.workers.tasks.auto_investigate_pending_claims")
def auto_investigate_pending_claims():
    """Every 10 min: run agentic AI on all PENDING claims with fraud_score >= 30."""
    result = _run(_do_auto_investigate())
    print(f"[Celery] Auto-investigate: {result}")
    return result


async def _do_auto_investigate():
    from app.database import AsyncSessionLocal
    from sqlalchemy import select
    from app.models.models import Claim, ClaimStatus
    from app.services.agentic_service import investigate_claim
    from app.services.notification_service import notify_claim_approved, notify_claim_rejected
    import json

    now = datetime.now(timezone.utc)
    investigated = 0
    approved = 0
    rejected = 0

    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Claim).where(
                Claim.status == ClaimStatus.PENDING,
                Claim.fraud_score >= 30,
                Claim.ai_investigation.is_(None),
            ).order_by(Claim.created_at.asc()).limit(50)
        )
        pending_claims = result.scalars().all()

        for claim in pending_claims:
            try:
                from app.models.models import Worker, DisruptionEvent
                worker_result = await db.execute(select(Worker).where(Worker.id == claim.worker_id))
                worker = worker_result.scalar_one_or_none()
                if not worker:
                    continue

                investigation = await investigate_claim(claim.id, db)
                if "error" in investigation:
                    continue

                claim.ai_investigation = json.dumps(investigation)

                if investigation["verdict"] == "APPROVED":
                    claim.status = ClaimStatus.APPROVED
                    claim.processed_at = now
                    if not claim.approved_amount:
                        claim.approved_amount = round(claim.claimed_amount * 0.8, 2)
                    from app.models.models import Policy
                    policy_result = await db.execute(select(Policy).where(Policy.id == claim.policy_id))
                    policy = policy_result.scalar_one_or_none()
                    if policy:
                        policy.total_claimed = round(float(policy.total_claimed or 0) + (claim.approved_amount or 0), 2)
                        policy.claims_count = (policy.claims_count or 0) + 1
                    event_result = await db.execute(select(DisruptionEvent).where(DisruptionEvent.id == claim.disruption_event_id))
                    event = event_result.scalar_one_or_none()
                    if event:
                        await notify_claim_approved(db, worker, claim, event.disruption_type.value)
                    approved += 1
                else:
                    claim.status = ClaimStatus.REJECTED
                    claim.processed_at = now
                    claim.rejection_reason = investigation["explanation"]
                    penalty = investigation.get("penalty", 0)
                    if penalty > 0:
                        worker.penalty_score = round(float(worker.penalty_score or 0) + penalty, 1)
                        worker.risk_score = min(1.0, round(float(worker.risk_score or 0.5) + penalty / 100.0, 3))
                    await notify_claim_rejected(db, worker, claim)
                    rejected += 1

                investigated += 1
                await db.commit()
            except Exception as e:
                print(f"[AutoInvestigate] ERROR on claim {claim.id}: {e}")
                await db.rollback()
                continue

    return {"investigated": investigated, "approved": approved, "rejected": rejected}
