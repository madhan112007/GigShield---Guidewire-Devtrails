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
# How long a disruption typically blocks a delivery worker
_BASE_DURATION_HOURS = {
    "heavy_rain": {"moderate": 1.5, "severe": 3.0, "extreme": 6.0},
    "extreme_heat": {"moderate": 4.0, "severe": 6.0, "extreme": 10.0},
    "aqi_spike": {"moderate": 4.0, "severe": 8.0, "extreme": 12.0},
    "traffic_disruption": {"moderate": 1.0, "severe": 2.5, "extreme": 5.0},
    "civic_emergency": {"moderate": 4.0, "severe": 8.0, "extreme": 16.0},
}

TOTAL_ACTIVE_HOURS = 16.0  # 6am to 10pm


async def get_infra_adjusted_dss(
    base_dss: float,
    city: str,
    pincode: str,
    disruption_type: str = "heavy_rain",
    severity: str = "severe",
) -> tuple[float, float, float]:
    """
    Adjust both DSS and effective hours ratio based on ward-level infrastructure.
    Returns (adjusted_dss, adjusted_hours_ratio, infra_score).

    Poor infra (bad drainage) = disruption lasts longer + income loss is higher.
    Good infra (good drainage) = disruption clears faster + lower income loss.

    Examples:
    - Heavy rain severe in Dharavi (infra=0.92):
        base_duration=3hrs → actual=4.8hrs → hours_ratio=0.30
        base_dss=0.60 → adjusted=0.82
    - Heavy rain severe in Gurgaon (infra=0.42):
        base_duration=3hrs → actual=1.8hrs → hours_ratio=0.11
        base_dss=0.60 → adjusted=0.58

    Heat, AQI, civic emergencies: infra affects duration but not DSS severity.
    Rain, traffic: infra affects both duration and DSS.
    """
    # Heat, AQI, civic: infra doesn't change severity, only duration
    infra_affects_dss = disruption_type in ("heavy_rain", "traffic_disruption")

    try:
        infra = await get_infra_score(city, pincode)
    except Exception:
        infra = 0.65  # neutral fallback

    # Duration factor: poor infra = longer disruption
    # infra 0.30 → factor 0.70 (clears fast)
    # infra 1.00 → factor 1.60 (stays long)
    duration_factor = round(0.70 + (infra - 0.30) * (0.90 / 0.70), 3)
    duration_factor = max(0.70, min(1.60, duration_factor))

    base_duration = _BASE_DURATION_HOURS.get(
        disruption_type, {}
    ).get(severity, 3.0)

    actual_duration = min(base_duration * duration_factor, TOTAL_ACTIVE_HOURS)
    adjusted_hours_ratio = round(actual_duration / TOTAL_ACTIVE_HOURS, 3)

    # DSS amplifier: only for rain and traffic
    if infra_affects_dss:
        dss_amplifier = round(0.85 + (infra - 0.30) * (0.55 / 0.70), 3)
        dss_amplifier = max(0.85, min(1.40, dss_amplifier))
        adjusted_dss = round(min(base_dss * dss_amplifier, 1.0), 3)
    else:
        adjusted_dss = base_dss

    return adjusted_dss, adjusted_hours_ratio, infra
_cache: dict[str, float] = {}

# Known infra scores for major cities (used as fallback + cache seed)
_KNOWN_SCORES = {
    # Metro cities
    "Delhi": 0.35, "Mumbai": 0.55, "Bangalore": 0.60, "Chennai": 0.50,
    "Hyderabad": 0.45, "Pune": 0.50, "Kolkata": 0.60,
    # Tier-2
    "Ahmedabad": 0.50, "Jaipur": 0.55, "Lucknow": 0.60, "Surat": 0.50,
    "Kanpur": 0.65, "Nagpur": 0.55, "Indore": 0.55, "Bhopal": 0.60,
    "Visakhapatnam": 0.55, "Patna": 0.80, "Vadodara": 0.52,
    "Coimbatore": 0.52, "Madurai": 0.58, "Kochi": 0.48,
    "Chandigarh": 0.40, "Guwahati": 0.70, "Dehradun": 0.58,
    "Noida": 0.45, "Gurgaon": 0.42, "Faridabad": 0.55,
    "Amritsar": 0.55, "Ludhiana": 0.58, "Jalandhar": 0.58,
    "Bhubaneswar": 0.55, "Ranchi": 0.68, "Raipur": 0.65,
    "Jodhpur": 0.60, "Udaipur": 0.58, "Ajmer": 0.62,
    "Mysore": 0.52, "Hubli": 0.60, "Mangalore": 0.52,
    "Tiruchirappalli": 0.55, "Salem": 0.58, "Erode": 0.58,
    "Warangal": 0.62, "Karimnagar": 0.65, "Khammam": 0.68,
    "Vijayawada": 0.55, "Guntur": 0.58, "Nellore": 0.60,
    # Tier-3 / rural
    "Patna": 0.80, "Gaya": 0.85, "Muzaffarpur": 0.85,
    "Varanasi": 0.70, "Allahabad": 0.68, "Gorakhpur": 0.72,
    "Agra": 0.65, "Meerut": 0.62, "Bareilly": 0.68,
    "Siliguri": 0.70, "Asansol": 0.68, "Durgapur": 0.65,
    "Imphal": 0.78, "Shillong": 0.72, "Aizawl": 0.75,
    "Itanagar": 0.80, "Kohima": 0.78, "Agartala": 0.75,
}

# Pincode prefix → infra score override (3-digit prefix)
_PINCODE_PREFIX_SCORES = {
    "110": 0.30,  # Central Delhi
    "400": 0.50,  # Mumbai central
    "560": 0.58,  # Bangalore central
    "600": 0.48,  # Chennai central
    "500": 0.42,  # Hyderabad central
    "411": 0.48,  # Pune central
    "700": 0.58,  # Kolkata central
    "380": 0.48,  # Ahmedabad central
    "302": 0.52,  # Jaipur central
    "226": 0.58,  # Lucknow central
    "800": 0.82,  # Patna — poor infra
    "781": 0.72,  # Guwahati
    "248": 0.56,  # Dehradun
    "201": 0.44,  # Noida
    "122": 0.40,  # Gurgaon
}


def _cache_key(city: str, pincode: str) -> str:
    return hashlib.md5(f"{city.lower()}:{pincode}".encode()).hexdigest()[:8]


def _fallback_score(city: str, pincode: str) -> float:
    """Rule-based fallback using known scores and pincode prefix heuristics."""
    # Check pincode prefix first (more granular)
    if len(pincode) >= 3:
        prefix_score = _PINCODE_PREFIX_SCORES.get(pincode[:3])
        if prefix_score:
            return prefix_score
    # Check known city scores
    for known_city, score in _KNOWN_SCORES.items():
        if known_city.lower() in city.lower() or city.lower() in known_city.lower():
            return score
    # Unknown location — use moderate score
    return 0.65


async def get_infra_adjusted_dss(
    base_dss: float,
    city: str,
    pincode: str,
    disruption_type: str = "heavy_rain",
) -> tuple[float, float]:
    """
    Adjust DSS based on ward-level infrastructure score from Gemini AI.
    Returns (adjusted_dss, infra_score).

    Poor infra (flooding, bad roads) amplifies income loss.
    Good infra (drainage, metro) reduces income loss.

    Only rain and traffic are infra-sensitive.
    Heat, AQI, civic emergencies affect workers regardless of infra.

    Amplifier range: 0.85 (excellent infra) to 1.40 (very poor infra)
    Fallback: base_dss unchanged if Gemini unavailable.
    """
    # Heat, AQI, civic emergencies are infra-independent
    if disruption_type in ("extreme_heat", "aqi_spike", "civic_emergency"):
        return base_dss, 0.65

    try:
        infra = await get_infra_score(city, pincode)
    except Exception:
        return base_dss, 0.65

    # Map infra score 0.30→0.85 and 1.0→1.40 linearly
    amplifier = round(0.85 + (infra - 0.30) * (0.55 / 0.70), 3)
    amplifier = max(0.85, min(1.40, amplifier))
    adjusted_dss = round(min(base_dss * amplifier, 1.0), 3)
    return adjusted_dss, infra
    """
    Get infrastructure resilience score for a location.
    Lower = better infra (lower risk premium).
    Higher = poor infra (higher risk premium).
    Range: 0.30 (excellent) to 1.0 (very poor)
    """
    key = _cache_key(city, pincode)
    if key in _cache:
        return _cache[key]

    # Try Gemini AI scoring first
    try:
        score = await _ai_score(city, pincode)
        _cache[key] = score
        return score
    except Exception:
        pass

    # Fallback to rule-based
    score = _fallback_score(city, pincode)
    _cache[key] = score
    return score


async def _ai_score(city: str, pincode: str) -> float:
    """
    Ask Gemini to score infrastructure quality for insurance risk pricing.
    Returns a float between 0.3 and 1.0.
    """
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
                "generationConfig": {
                    "temperature": 0.1,
                    "maxOutputTokens": 80,
                },
            },
        )
        data = res.json()
        content = data["candidates"][0]["content"]["parts"][0]["text"].strip()
        # Strip markdown code fences if present
        content = content.replace("```json", "").replace("```", "").strip()
        parsed = json.loads(content)
        score = float(parsed["score"])
        return max(0.30, min(1.0, score))
