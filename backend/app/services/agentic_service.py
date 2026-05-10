"""
Agentic AI Claim Investigation Service
=======================================
Runs a multi-step autonomous investigation on PENDING claims with fraud_score >= 30.

Agent steps (in order):
  Step 1 — Re-score eligibility with fresh data (re-runs fraud engine)
  Step 2 — GPS corroboration  (were there real pings near the event zone?)
  Step 3 — Zone corroboration (did other workers in the same zone also claim?)
  Step 4 — Claim history pattern (is this worker's history consistent?)
  Step 5 — Event legitimacy   (is the disruption event itself credible?)
  Step 6 — Final verdict      (weighted decision across all steps)

Returns:
  {
    "verdict":      "APPROVED" | "REJECTED",
    "confidence":   0-100,
    "penalty":      0 | 5 | 10 | 20   (added to worker.penalty_score if REJECTED)
    "explanation":  "Human-readable multi-line summary",
    "steps":        [ { "step": str, "result": str, "weight": float, "passed": bool } ]
  }
"""
from __future__ import annotations
import json
from datetime import datetime, timedelta, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func


async def investigate_claim(claim_id: str, db: AsyncSession) -> dict:
    from app.models.models import (
        Claim, Worker, DisruptionEvent, WorkerLocationPing,
        ClaimStatus, WorkerNotification,
    )

    # ── Load claim + worker + event ───────────────────────────────────────────
    result = await db.execute(
        select(Claim, Worker, DisruptionEvent)
        .join(Worker, Claim.worker_id == Worker.id)
        .join(DisruptionEvent, Claim.disruption_event_id == DisruptionEvent.id)
        .where(Claim.id == claim_id)
    )
    row = result.first()
    if not row:
        return {"error": "Claim not found"}

    claim, worker, event = row
    now = datetime.now(timezone.utc)
    steps = []

    # ── Step 1: Re-score eligibility ──────────────────────────────────────────
    from app.services.fraud_service import calculate_fraud_score
    week_ago = now - timedelta(days=7)
    claims_this_week = (await db.execute(
        select(func.count(Claim.id)).where(
            Claim.worker_id == worker.id,
            Claim.created_at >= week_ago,
            Claim.id != claim_id,
        )
    )).scalar() or 0

    hist_count = (await db.execute(
        select(func.count(Claim.id)).where(
            Claim.worker_id == worker.id,
            Claim.created_at >= now - timedelta(weeks=12),
        )
    )).scalar() or 0
    avg_claims_per_week = round(hist_count / 12.0, 2) if hist_count > 0 else 0.0

    event_started_at = event.started_at
    if event_started_at.tzinfo is None:
        event_started_at = event_started_at.replace(tzinfo=timezone.utc)
    claim_created_at = claim.created_at
    if claim_created_at.tzinfo is None:
        claim_created_at = claim_created_at.replace(tzinfo=timezone.utc)

    fresh_fraud = calculate_fraud_score(
        worker_city=worker.city,
        event_city=event.city,
        worker_pincode=worker.pincode,
        event_pincode=event.pincode or "",
        was_platform_active=True,
        claims_this_week=claims_this_week,
        claims_same_event=0,
        event_started_at=event_started_at,
        claim_created_at=claim_created_at,
        disruption_type=event.disruption_type,
        worker_avg_claims_per_week=avg_claims_per_week,
    )
    fresh_score = fresh_fraud["fraud_score"]
    step1_passed = fresh_score < 50
    steps.append({
        "step": "Eligibility Re-Score",
        "result": f"Fresh fraud score: {fresh_score:.0f}/100 — {'within threshold' if step1_passed else 'still elevated'}",
        "weight": 0.30,
        "passed": step1_passed,
    })

    # ── Step 2: GPS corroboration ─────────────────────────────────────────────
    ping_window_start = event_started_at - timedelta(hours=1)
    ping_window_end   = event_started_at + timedelta(hours=3)
    pings = (await db.execute(
        select(WorkerLocationPing).where(
            WorkerLocationPing.worker_id == worker.id,
            WorkerLocationPing.recorded_at >= ping_window_start,
            WorkerLocationPing.recorded_at <= ping_window_end,
            WorkerLocationPing.is_suspicious == False,
        )
    )).scalars().all()

    gps_ok = len(pings) >= 1
    if gps_ok and event.lat and event.lng:
        import math
        def _hav(lat1, lon1, lat2, lon2):
            R = 6371
            dlat = math.radians(lat2 - lat1)
            dlon = math.radians(lon2 - lon1)
            a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
            return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        radius = event.radius_km or 10.0
        near_pings = [p for p in pings if _hav(p.lat, p.lng, event.lat, event.lng) <= radius * 2]
        gps_ok = len(near_pings) >= 1
        gps_detail = f"{len(near_pings)}/{len(pings)} pings within {radius*2:.0f}km of event zone"
    elif gps_ok:
        gps_detail = f"{len(pings)} GPS pings found during event window (no event coords to cross-check)"
    else:
        gps_detail = "No GPS pings found during event window — location unverifiable"

    steps.append({
        "step": "GPS Corroboration",
        "result": gps_detail,
        "weight": 0.25,
        "passed": gps_ok,
    })

    # ── Step 3: Zone corroboration ────────────────────────────────────────────
    zone_prefix = worker.pincode[:3] if worker.pincode else ""
    from app.models.models import Worker as WorkerModel
    zone_workers = (await db.execute(
        select(func.count(WorkerModel.id)).where(
            WorkerModel.pincode.like(f"{zone_prefix}%"),
            WorkerModel.is_active == True,
        )
    )).scalar() or 0

    zone_claims = (await db.execute(
        select(func.count(Claim.id)).where(
            Claim.disruption_event_id == event.id,
        ).join(WorkerModel, Claim.worker_id == WorkerModel.id)
        .where(WorkerModel.pincode.like(f"{zone_prefix}%"))
    )).scalar() or 0

    if zone_workers > 3:
        zone_rate = zone_claims / zone_workers
        zone_ok = 0.03 <= zone_rate <= 0.90
        zone_detail = f"{zone_claims}/{zone_workers} workers in zone {zone_prefix}xxx claimed ({zone_rate:.0%})"
        if zone_rate < 0.03:
            zone_detail += " — very low corroboration"
        elif zone_rate > 0.90:
            zone_detail += " — suspiciously high (possible coordinated fraud)"
        else:
            zone_detail += " — corroboration looks normal"
    else:
        zone_ok = True  # not enough zone data to penalise
        zone_detail = f"Insufficient zone data ({zone_workers} workers in zone) — skipping zone check"

    steps.append({
        "step": "Zone Corroboration",
        "result": zone_detail,
        "weight": 0.20,
        "passed": zone_ok,
    })

    # ── Step 4: Claim history pattern ─────────────────────────────────────────
    approved_claims = (await db.execute(
        select(func.count(Claim.id)).where(
            Claim.worker_id == worker.id,
            Claim.status.in_(["approved", "paid"]),
        )
    )).scalar() or 0

    rejected_claims = (await db.execute(
        select(func.count(Claim.id)).where(
            Claim.worker_id == worker.id,
            Claim.status == "rejected",
        )
    )).scalar() or 0

    total_past = approved_claims + rejected_claims
    rejection_rate = rejected_claims / total_past if total_past > 0 else 0.0
    history_ok = rejection_rate < 0.5 and claims_this_week <= 4

    if total_past == 0:
        history_detail = "New worker — no prior claim history to evaluate"
        history_ok = True
    else:
        history_detail = (
            f"{approved_claims} approved, {rejected_claims} rejected "
            f"({rejection_rate:.0%} rejection rate) — "
            f"{'acceptable' if history_ok else 'high rejection rate or excessive frequency'}"
        )

    steps.append({
        "step": "Claim History Pattern",
        "result": history_detail,
        "weight": 0.15,
        "passed": history_ok,
    })

    # ── Step 5: Event legitimacy ──────────────────────────────────────────────
    total_claims_on_event = (await db.execute(
        select(func.count(Claim.id)).where(Claim.disruption_event_id == event.id)
    )).scalar() or 0

    event_age_hours = (now - event_started_at).total_seconds() / 3600
    event_ok = (
        event.is_active or event_age_hours <= 48
    ) and total_claims_on_event >= 1

    event_detail = (
        f"Event '{event.disruption_type.value}' in {event.city} — "
        f"{'active' if event.is_active else f'ended {event_age_hours:.0f}h ago'}, "
        f"{total_claims_on_event} total claims on this event"
    )

    steps.append({
        "step": "Event Legitimacy",
        "result": event_detail,
        "weight": 0.10,
        "passed": event_ok,
    })

    # ── Step 6: Final weighted verdict ────────────────────────────────────────
    passed_weight = sum(s["weight"] for s in steps if s["passed"])
    total_weight  = sum(s["weight"] for s in steps)
    confidence    = round((passed_weight / total_weight) * 100)
    verdict       = "APPROVED" if confidence >= 55 else "REJECTED"

    # Penalty scoring: only on REJECTED, scaled by how badly it failed
    penalty = 0
    if verdict == "REJECTED":
        failed_steps = [s for s in steps if not s["passed"]]
        if len(failed_steps) >= 4:
            penalty = 20
        elif len(failed_steps) == 3:
            penalty = 10
        elif len(failed_steps) == 2:
            penalty = 5

    # Build human-readable explanation
    lines = [f"Agent investigated {len(steps)} signals. Confidence: {confidence}%."]
    for s in steps:
        icon = "✅" if s["passed"] else "❌"
        lines.append(f"{icon} {s['step']}: {s['result']}")
    if verdict == "APPROVED":
        lines.append(f"\nVerdict: APPROVED — sufficient evidence supports this claim.")
    else:
        lines.append(f"\nVerdict: REJECTED — claim does not meet approval threshold.")
        if penalty > 0:
            lines.append(f"Penalty: +{penalty} points added to worker trust score.")

    return {
        "verdict":     verdict,
        "confidence":  confidence,
        "penalty":     penalty,
        "explanation": "\n".join(lines),
        "steps":       steps,
        "fresh_fraud_score": fresh_score,
    }
