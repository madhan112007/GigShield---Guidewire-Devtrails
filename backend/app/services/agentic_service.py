"""
Agentic AI Claim Investigation Service
=======================================
Uses Google Gemini 2.5 Flash as the reasoning brain.

Flow:
  1. Run 5 evidence-gathering steps (pure DB queries — no AI yet)
  2. Package all evidence into a structured prompt
  3. Send to Gemini 2.5 Flash — it reasons over the evidence and returns:
       { verdict, confidence, explanation, penalty, step_verdicts }
  4. If Gemini fails (timeout / quota) → fall back to weighted scoring

Evidence steps:
  Step 1 — Eligibility Re-Score      (weight 30%)
  Step 2 — GPS Corroboration         (weight 25%)
  Step 3 — Zone Corroboration        (weight 20%)
  Step 4 — Claim History Pattern     (weight 15%)
  Step 5 — Event Legitimacy          (weight 10%)
"""
from __future__ import annotations
import json
import httpx
from datetime import datetime, timedelta, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.config import settings


# ── Gemini call ───────────────────────────────────────────────────────────────

_GEMINI_URL = (
    "https://generativelanguage.googleapis.com/v1beta"
    "/models/gemini-2.5-flash:generateContent"
)

_SYSTEM_PROMPT = """You are an insurance claim investigation AI for Susanoo, 
an income-protection insurance platform for gig delivery workers in India.

Your job is to review evidence gathered about a flagged insurance claim and 
decide whether it should be APPROVED or REJECTED.

You will receive:
- Worker profile (city, platform, earnings, history)
- Claim details (amount, disruption type, fraud score)
- Results from 5 evidence-gathering steps

Rules:
- Be fair to workers — they are low-income gig workers who depend on this income
- A single suspicious signal is NOT enough to reject — look at the full picture
- GPS absence alone is not fraud — many workers have old phones with poor GPS
- Zone corroboration is strong evidence — if many workers in the same area claimed, the event was real
- Clean claim history is a strong positive signal
- High fraud score (50+) combined with GPS absence AND low zone corroboration = reject

Respond ONLY with a valid JSON object in this exact format:
{
  "verdict": "APPROVED" or "REJECTED",
  "confidence": <integer 0-100>,
  "penalty": <integer: 0, 5, 10, or 20>,
  "explanation": "<2-4 sentences explaining your reasoning in plain English, mentioning the key signals that drove your decision>",
  "step_verdicts": {
    "eligibility_rescore": "pass" or "fail",
    "gps_corroboration": "pass" or "fail",
    "zone_corroboration": "pass" or "fail",
    "claim_history": "pass" or "fail",
    "event_legitimacy": "pass" or "fail"
  }
}

Penalty guide:
- 0  → APPROVED, or REJECTED but borderline (1-2 weak signals)
- 5  → REJECTED with 2 clear signals
- 10 → REJECTED with 3 clear signals
- 20 → REJECTED with 4+ clear signals (strong fraud indicators)
"""


async def _call_gemini(evidence: dict) -> dict | None:
    """Send evidence to Gemini 2.5 Flash and parse the JSON response."""
    api_key = settings.GEMINI_API_KEY.strip()
    if not api_key or api_key == "your_gemini_api_key_here":
        return None

    prompt = f"{_SYSTEM_PROMPT}\n\nEvidence to investigate:\n{json.dumps(evidence, indent=2, default=str)}"

    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            r = await client.post(
                f"{_GEMINI_URL}?key={api_key}",
                json={
                    "contents": [{"parts": [{"text": prompt}]}],
                    "generationConfig": {
                        "temperature": 0.1,       # low temp = consistent, factual
                        "maxOutputTokens": 512,
                    },
                },
            )
            if r.status_code != 200:
                print(f"[Gemini] HTTP {r.status_code}: {r.text[:200]}")
                return None

            data = r.json()
            raw_text = (
                data.get("candidates", [{}])[0]
                .get("content", {})
                .get("parts", [{}])[0]
                .get("text", "")
            )

            # Strip markdown code fences if Gemini wraps in ```json ... ```
            clean = raw_text.strip()
            if clean.startswith("```"):
                clean = clean.split("```")[1]
                if clean.startswith("json"):
                    clean = clean[4:]
            clean = clean.strip()

            result = json.loads(clean)
            # Validate required fields
            if "verdict" not in result or result["verdict"] not in ("APPROVED", "REJECTED"):
                return None
            return result

    except (httpx.HTTPError, json.JSONDecodeError, KeyError, IndexError) as e:
        print(f"[Gemini] Error: {e}")
        return None


# ── Fallback weighted scoring ─────────────────────────────────────────────────

def _weighted_fallback(steps: list[dict]) -> dict:
    """Original weighted scoring — used when Gemini is unavailable."""
    passed_weight = sum(s["weight"] for s in steps if s["passed"])
    total_weight = sum(s["weight"] for s in steps)
    confidence = round((passed_weight / total_weight) * 100)
    verdict = "APPROVED" if confidence >= 55 else "REJECTED"

    penalty = 0
    if verdict == "REJECTED":
        failed = sum(1 for s in steps if not s["passed"])
        if failed >= 4:
            penalty = 20
        elif failed == 3:
            penalty = 10
        elif failed == 2:
            penalty = 5

    lines = [f"[Fallback scoring — Gemini unavailable] Confidence: {confidence}%."]
    for s in steps:
        icon = "✅" if s["passed"] else "❌"
        lines.append(f"{icon} {s['step']}: {s['result']}")
    if verdict == "APPROVED":
        lines.append("Verdict: APPROVED — sufficient evidence supports this claim.")
    else:
        lines.append("Verdict: REJECTED — claim does not meet approval threshold.")
        if penalty > 0:
            lines.append(f"Penalty: +{penalty} points added to worker trust score.")

    return {
        "verdict": verdict,
        "confidence": confidence,
        "penalty": penalty,
        "explanation": "\n".join(lines),
        "steps": steps,
        "gemini_used": False,
    }


# ── Main investigation entry point ────────────────────────────────────────────

async def investigate_claim(claim_id: str, db: AsyncSession) -> dict:
    from app.models.models import (
        Claim, Worker, DisruptionEvent,
        WorkerLocationPing, ClaimStatus,
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

    event_started_at = event.started_at
    if event_started_at.tzinfo is None:
        event_started_at = event_started_at.replace(tzinfo=timezone.utc)
    claim_created_at = claim.created_at
    if claim_created_at.tzinfo is None:
        claim_created_at = claim_created_at.replace(tzinfo=timezone.utc)

    # ── Step 1: Eligibility Re-Score ──────────────────────────────────────────
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
        "result": f"Fresh fraud score: {fresh_score:.0f}/100 — {'within threshold' if step1_passed else 'still elevated'}. Flags: {fresh_fraud['flags'] or 'none'}",
        "weight": 0.30,
        "passed": step1_passed,
    })

    # ── Step 2: GPS Corroboration ─────────────────────────────────────────────
    ping_window_start = event_started_at - timedelta(hours=1)
    ping_window_end = event_started_at + timedelta(hours=3)
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
        gps_detail = f"{len(near_pings)}/{len(pings)} pings within {radius*2:.0f}km of event zone during disruption window"
    elif gps_ok:
        gps_detail = f"{len(pings)} GPS pings found during event window (no event coordinates to cross-check location)"
    else:
        gps_detail = "No GPS pings found during event window — worker location during disruption is unverifiable"

    steps.append({
        "step": "GPS Corroboration",
        "result": gps_detail,
        "weight": 0.25,
        "passed": gps_ok,
    })

    # ── Step 3: Zone Corroboration ────────────────────────────────────────────
    zone_prefix = worker.pincode[:3] if worker.pincode else ""
    from app.models.models import Worker as WorkerModel
    zone_workers = (await db.execute(
        select(func.count(WorkerModel.id)).where(
            WorkerModel.pincode.like(f"{zone_prefix}%"),
            WorkerModel.is_active == True,
        )
    )).scalar() or 0

    zone_claims = (await db.execute(
        select(func.count(Claim.id))
        .join(WorkerModel, Claim.worker_id == WorkerModel.id)
        .where(
            Claim.disruption_event_id == event.id,
            WorkerModel.pincode.like(f"{zone_prefix}%"),
        )
    )).scalar() or 0

    if zone_workers > 3:
        zone_rate = zone_claims / zone_workers
        zone_ok = 0.03 <= zone_rate <= 0.90
        zone_detail = (
            f"{zone_claims}/{zone_workers} workers in zone {zone_prefix}xxx claimed "
            f"({zone_rate:.1%}) — "
            + ("very low corroboration, event not confirmed by peers" if zone_rate < 0.03
               else "suspiciously high, possible coordinated fraud ring" if zone_rate > 0.90
               else "corroboration rate looks normal")
        )
    else:
        zone_ok = True
        zone_detail = f"Only {zone_workers} workers in zone — insufficient data for zone analysis, skipping"

    steps.append({
        "step": "Zone Corroboration",
        "result": zone_detail,
        "weight": 0.20,
        "passed": zone_ok,
    })

    # ── Step 4: Claim History Pattern ─────────────────────────────────────────
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
        history_detail = "New worker with no prior claim history — benefit of the doubt applied"
        history_ok = True
    else:
        history_detail = (
            f"{approved_claims} approved, {rejected_claims} rejected out of {total_past} total "
            f"({rejection_rate:.0%} rejection rate), {claims_this_week} claims this week — "
            f"{'history looks acceptable' if history_ok else 'high rejection rate or excessive frequency this week'}"
        )

    steps.append({
        "step": "Claim History Pattern",
        "result": history_detail,
        "weight": 0.15,
        "passed": history_ok,
    })

    # ── Step 5: Event Legitimacy ──────────────────────────────────────────────
    total_claims_on_event = (await db.execute(
        select(func.count(Claim.id)).where(Claim.disruption_event_id == event.id)
    )).scalar() or 0

    event_age_hours = (now - event_started_at).total_seconds() / 3600
    event_ok = (event.is_active or event_age_hours <= 48) and total_claims_on_event >= 1
    event_detail = (
        f"Event '{event.disruption_type.value.replace('_', ' ')}' in {event.city} — "
        f"{'currently active' if event.is_active else f'ended {event_age_hours:.0f}h ago'}, "
        f"severity: {event.severity.value}, "
        f"{total_claims_on_event} total claim(s) filed against this event"
    )

    steps.append({
        "step": "Event Legitimacy",
        "result": event_detail,
        "weight": 0.10,
        "passed": event_ok,
    })

    # ── Build evidence package for Gemini ─────────────────────────────────────
    evidence = {
        "worker": {
            "name": worker.name,
            "city": worker.city,
            "platform": worker.platform.value if worker.platform else "unknown",
            "avg_daily_earnings_inr": worker.avg_daily_earnings,
            "penalty_score": worker.penalty_score or 0,
            "risk_score": worker.risk_score,
        },
        "claim": {
            "claimed_amount_inr": claim.claimed_amount,
            "disruption_type": event.disruption_type.value,
            "disruption_severity": event.severity.value,
            "original_fraud_score": claim.fraud_score,
            "original_fraud_flags": json.loads(claim.fraud_flags or "[]"),
            "time_since_event_start_seconds": (claim_created_at - event_started_at).total_seconds(),
        },
        "evidence_steps": [
            {
                "step": s["step"],
                "passed": s["passed"],
                "detail": s["result"],
                "weight_in_decision": f"{int(s['weight']*100)}%",
            }
            for s in steps
        ],
    }

    # ── Call Gemini ───────────────────────────────────────────────────────────
    gemini_result = await _call_gemini(evidence)

    if gemini_result:
        print(f"[Gemini] Verdict: {gemini_result['verdict']} | Confidence: {gemini_result['confidence']}%")

        # Map Gemini's step_verdicts back onto our steps list for UI display
        sv = gemini_result.get("step_verdicts", {})
        step_key_map = {
            "Eligibility Re-Score":   "eligibility_rescore",
            "GPS Corroboration":      "gps_corroboration",
            "Zone Corroboration":     "zone_corroboration",
            "Claim History Pattern":  "claim_history",
            "Event Legitimacy":       "event_legitimacy",
        }
        for s in steps:
            key = step_key_map.get(s["step"])
            if key and key in sv:
                s["passed"] = sv[key] == "pass"

        return {
            "verdict":           gemini_result["verdict"],
            "confidence":        gemini_result["confidence"],
            "penalty":           gemini_result.get("penalty", 0),
            "explanation":       gemini_result["explanation"],
            "steps":             steps,
            "fresh_fraud_score": fresh_score,
            "gemini_used":       True,
            "model":             "gemini-2.5-flash",
        }

    # ── Fallback ──────────────────────────────────────────────────────────────
    print("[Gemini] Unavailable — falling back to weighted scoring")
    return _weighted_fallback(steps)
