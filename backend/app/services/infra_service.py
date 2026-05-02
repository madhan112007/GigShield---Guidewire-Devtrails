"""
AI-Powered Infrastructure Scoring Service
Uses Google Gemini to dynamically score any Indian city/pincode for infrastructure quality.
Score range: 0.3 (excellent infra, low risk) to 1.0 (poor infra, high risk)
Falls back to rule-based heuristics if AI is unavailable.
"""
import json
import hashlib
import httpx
from app.config import settings

_GEMINI_API_KEY = settings.GEMINI_API_KEY
_GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent"

# Base disruption durations in hours by type and severity
_BASE_DURATION_HOURS = {
    "heavy_rain":         {"moderate": 1.5, "severe": 3.0, "extreme": 6.0},
    "extreme_heat":       {"moderate": 4.0, "severe": 6.0, "extreme": 10.0},
    "aqi_spike":          {"moderate": 4.0, "severe": 8.0, "extreme": 12.0},
    "traffic_disruption": {"moderate": 1.0, "severe": 2.5, "extreme": 5.0},
    "civic_emergency":    {"moderate": 4.0, "severe": 8.0, "extreme": 16.0},
}

TOTAL_ACTIVE_HOURS = 16.0  # 6am to 10pm

# In-memory cache — avoids repeated API calls for same pincode
_cache: dict[str, float] = {}

# Known infra scores for major cities (fallback)
_KNOWN_SCORES = {
    "Delhi": 0.35, "Mumbai": 0.55, "Bangalore": 0.60, "Chennai": 0.50,
    "Hyderabad": 0.45, "Pune": 0.50, "Kolkata": 0.60,
    "Ahmedabad": 0.50, "Jaipur": 0.55, "Lucknow": 0.60, "Surat": 0.50,
    "Kanpur": 0.65, "Nagpur": 0.55, "Indore": 0.55, "Bhopal": 0.60,
    "Visakhapatnam": 0.55, "Patna": 0.80, "Vadodara": 0.52,
    "Coimbatore": 0.52, "Madurai": 0.58, "Kochi": 0.48,
    "Chandigarh": 0.40, "Guwahati": 0.70, "Dehradun": 0.58,
    "Noida": 0.45, "Gurgaon": 0.42, "Faridabad": 0.55,
    "Amritsar": 0.55, "Ludhiana": 0.58, "Bhubaneswar": 0.55,
    "Ranchi": 0.68, "Raipur": 0.65, "Jodhpur": 0.60,
    "Mysore": 0.52, "Hubli": 0.60, "Mangalore": 0.52,
    "Tiruchirappalli": 0.55, "Salem": 0.58, "Erode": 0.58,
    "Warangal": 0.62, "Vijayawada": 0.55, "Guntur": 0.58,
    "Varanasi": 0.70, "Agra": 0.65, "Meerut": 0.62,
    "Siliguri": 0.70, "Imphal": 0.78, "Shillong": 0.72,
    "Patna": 0.80, "Gaya": 0.85,
}

_PINCODE_PREFIX_SCORES = {
    "110": 0.30, "400": 0.50, "560": 0.58, "600": 0.48,
    "500": 0.42, "411": 0.48, "700": 0.58, "380": 0.48,
    "302": 0.52, "226": 0.58, "800": 0.82, "781": 0.72,
    "248": 0.56, "201": 0.44, "122": 0.40,
}


def _cache_key(city: str, pincode: str) -> str:
    return hashlib.md5(f"{city.lower()}:{pincode}".encode()).hexdigest()[:8]


def _fallback_score(city: str, pincode: str) -> float:
    if len(pincode) >= 3:
        prefix_score = _PINCODE_PREFIX_SCORES.get(pincode[:3])
        if prefix_score:
            return prefix_score
    for known_city, score in _KNOWN_SCORES.items():
        if known_city.lower() in city.lower() or city.lower() in known_city.lower():
            return score
    return 0.65


async def get_infra_score(city: str, pincode: str) -> float:
    """
    Get infrastructure resilience score for a location.
    Lower = better infra. Higher = poor infra.
    Range: 0.30 (excellent) to 1.0 (very poor)
    """
    key = _cache_key(city, pincode)
    if key in _cache:
        return _cache[key]

    try:
        score = await _ai_score(city, pincode)
        _cache[key] = score
        return score
    except Exception:
        pass

    score = _fallback_score(city, pincode)
    _cache[key] = score
    return score


async def _ai_score(city: str, pincode: str) -> float:
    prompt = f"""You are an insurance actuary scoring Indian cities for infrastructure quality.
Score the following location for delivery worker income insurance risk pricing.

Location: {city}, India (Pincode: {pincode})

Consider:
1. Road quality and drainage infrastructure
2. Flood/waterlogging risk during monsoon
3. Heat island effect and extreme weather exposure
4. Traffic congestion and disruption frequency
5. Public transport and dark store density
6. Historical disaster frequency (IMD/NDMA data)

Return ONLY a JSON object with this exact format:
{{"score": 0.XX, "reason": "brief one-line reason"}}

Score guide:
- 0.30-0.40: Excellent infra (Central Delhi, Gurgaon, Chandigarh)
- 0.41-0.55: Good infra (Hyderabad, Kochi, Ahmedabad)
- 0.56-0.65: Moderate infra (Bangalore, Chennai, Pune)
- 0.66-0.80: Poor infra (Patna, Guwahati, tier-3 cities)
- 0.81-1.00: Very poor infra (rural, flood-prone districts)"""

    async with httpx.AsyncClient(timeout=8.0) as client:
        res = await client.post(
            f"{_GEMINI_URL}?key={_GEMINI_API_KEY}",
            json={
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {"temperature": 0.1, "maxOutputTokens": 80},
            },
        )
        data = res.json()
        content = data["candidates"][0]["content"]["parts"][0]["text"].strip()
        content = content.replace("```json", "").replace("```", "").strip()
        parsed = json.loads(content)
        score = float(parsed["score"])
        return max(0.30, min(1.0, score))


async def get_activity_zone_infra_score(
    worker_id: str,
    db,
    fallback_city: str = "",
    fallback_pincode: str = "",
    days: int = 30,
) -> float:
    """
    Calculate worker's activity zone infra score from last N days of GPS pings.

    Gig workers move across multiple wards daily. This builds a weighted infra
    score based on WHERE they actually spend their working time — not just their
    registered address or a single ping.

    Each unique pincode gets a weight proportional to how many pings came from it.
    More time in a ward = higher weight in the final score.

    Fallback: registered city/pincode if no GPS history.
    """
    from datetime import datetime, timezone, timedelta
    from sqlalchemy import select, func
    from app.models.models import WorkerLocationPing

    now = datetime.now(timezone.utc)
    since = now - timedelta(days=days)

    # Get ping counts grouped by pincode+city from last N days
    result = await db.execute(
        select(
            WorkerLocationPing.city_detected,
            WorkerLocationPing.pincode_detected,
            func.count(WorkerLocationPing.id).label("ping_count"),
        ).where(
            WorkerLocationPing.worker_id == worker_id,
            WorkerLocationPing.recorded_at >= since,
            WorkerLocationPing.city_detected.isnot(None),
            WorkerLocationPing.city_detected != "",
        ).group_by(
            WorkerLocationPing.city_detected,
            WorkerLocationPing.pincode_detected,
        ).order_by(func.count(WorkerLocationPing.id).desc())
    )
    rows = result.all()

    if not rows:
        # No GPS history — use registered location as fallback
        return await get_infra_score(fallback_city, fallback_pincode)

    total_pings = sum(r.ping_count for r in rows)
    weighted_score = 0.0

    for row in rows:
        weight = row.ping_count / total_pings
        city = row.city_detected or fallback_city
        pincode = row.pincode_detected or fallback_pincode
        score = await get_infra_score(city, pincode)
        weighted_score += score * weight

    return round(weighted_score, 3)


async def get_infra_adjusted_dss(
    base_dss: float,
    city: str,
    pincode: str,
    disruption_type: str = "heavy_rain",
    severity: str = "severe",
    activity_zone_infra: float = None,
) -> tuple[float, float, float]:
    """
    Adjust DSS and hours ratio based on infrastructure score.
    If activity_zone_infra is provided (from get_activity_zone_infra_score),
    uses that instead of single-location scoring.
    Returns (adjusted_dss, adjusted_hours_ratio, infra_score).
    """
    infra_affects_dss = disruption_type in ("heavy_rain", "traffic_disruption")

    if activity_zone_infra is not None:
        infra = activity_zone_infra
    else:
        try:
            infra = await get_infra_score(city, pincode)
        except Exception:
            infra = 0.65

    duration_factor = round(0.70 + (infra - 0.30) * (0.90 / 0.70), 3)
    duration_factor = max(0.70, min(1.60, duration_factor))

    base_duration = _BASE_DURATION_HOURS.get(disruption_type, {}).get(severity, 3.0)
    actual_duration = min(base_duration * duration_factor, TOTAL_ACTIVE_HOURS)
    adjusted_hours_ratio = round(actual_duration / TOTAL_ACTIVE_HOURS, 3)

    if infra_affects_dss:
        dss_amplifier = round(0.85 + (infra - 0.30) * (0.55 / 0.70), 3)
        dss_amplifier = max(0.85, min(1.40, dss_amplifier))
        adjusted_dss = round(min(base_dss * dss_amplifier, 1.0), 3)
    else:
        adjusted_dss = base_dss

    return adjusted_dss, adjusted_hours_ratio, infra
