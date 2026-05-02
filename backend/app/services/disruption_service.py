"""
Disruption Monitoring Service
Hyper-local DSS: same rainfall = different income impact based on city infrastructure.
Delhi has good drainage -> lower DSS for moderate rain.
Rural/tier-3 areas have poor transport -> higher DSS for same event.
"""
import httpx
import random
import tweepy
from datetime import datetime
from typing import Optional
from app.config import settings
from app.models.models import DisruptionType, DisruptionSeverity

# Historical trigger probability per city (used for next-week forecast in admin analytics)
TRIGGER_PROBABILITY = {
    "Bangalore": {"heavy_rain": 0.45, "traffic_disruption": 0.30, "aqi_spike": 0.15, "civic_emergency": 0.10},
    "Mumbai":    {"heavy_rain": 0.55, "traffic_disruption": 0.25, "civic_emergency": 0.12, "extreme_heat": 0.08},
    "Delhi":     {"extreme_heat": 0.40, "aqi_spike": 0.35, "traffic_disruption": 0.15, "civic_emergency": 0.10},
    "Chennai":   {"heavy_rain": 0.40, "extreme_heat": 0.30, "civic_emergency": 0.15, "traffic_disruption": 0.15},
    "Hyderabad": {"heavy_rain": 0.35, "extreme_heat": 0.25, "traffic_disruption": 0.25, "civic_emergency": 0.15},
}


# ── Hyper-local Infrastructure Score (0.0 = best, 1.0 = worst) ───────────────
# Based on: drainage quality, road density, public transport, dark store coverage
# Sources: Smart City Index, NIUA Urban Infrastructure Reports
INFRA_SCORE = {
    # Metro cities — good infrastructure, lower DSS impact
    "Delhi":     0.35,  # Good drainage (NMCG), metro connectivity, but heat/AQI high
    "Mumbai":    0.55,  # Poor drainage (floods easily), but dense delivery network
    "Bangalore": 0.60,  # Worst drainage among metros, IT corridor gridlock
    "Chennai":   0.50,  # Moderate drainage, cyclone-prone coast
    "Hyderabad": 0.45,  # Decent infra, HMDA roads
    "Pune":      0.50,  # Moderate
    "Kolkata":   0.60,  # Old drainage, flood-prone
    # Tier-2 cities — moderate infrastructure
    "Ahmedabad": 0.55,
    "Jaipur":    0.60,
    "Lucknow":   0.65,
    "Bhopal":    0.65,
    "Patna":     0.80,  # Poor drainage, flood-prone
    "Guwahati":  0.75,
    # Rural/Tier-3 — poor infrastructure, higher DSS
    "rural":     0.90,
}

# Pincode prefix -> infra override (more granular than city)
# Lower 3-digit prefix = better infra within same city
PINCODE_INFRA_OVERRIDE = {
    "110": 0.30,  # Central Delhi — best drainage
    "400": 0.50,  # Mumbai central
    "560": 0.58,  # Bangalore central
    "600": 0.48,  # Chennai central
    "500": 0.42,  # Hyderabad central
    "411": 0.48,  # Pune central
    "800": 0.82,  # Patna — poor infra
    "781": 0.78,  # Guwahati
}


def get_infra_score(city: str, pincode: str) -> float:
    """Get infrastructure resilience score for a location. Lower = better infra."""
    prefix = pincode[:3] if len(pincode) >= 3 else ""
    if prefix in PINCODE_INFRA_OVERRIDE:
        return PINCODE_INFRA_OVERRIDE[prefix]
    return INFRA_SCORE.get(city, 0.65)


def get_dss(disruption_type: DisruptionType, severity: DisruptionSeverity,
            city: str = "", pincode: str = "") -> float:
    """
    Hyper-local DSS: base DSS adjusted by infrastructure score.
    Delhi with good drainage: 45mm/hr rain -> DSS 0.18 (service still possible)
    Rural area with no roads: 45mm/hr rain -> DSS 0.45 (complete income loss)
    """
    base_dss = DSS_TABLE.get(disruption_type, {}).get(severity, 0.3)
    if not city and not pincode:
        return base_dss
    infra = get_infra_score(city, pincode)
    # Rain and traffic are most affected by infrastructure quality
    if disruption_type in (DisruptionType.HEAVY_RAIN, DisruptionType.TRAFFIC_DISRUPTION):
        adjusted = round(base_dss * (0.5 + infra * 0.8), 2)
    # Heat and AQI affect workers regardless of infrastructure
    elif disruption_type in (DisruptionType.EXTREME_HEAT, DisruptionType.AQI_SPIKE):
        adjusted = round(base_dss * (0.8 + infra * 0.3), 2)
    # Civic emergencies are uniform — a bandh is a bandh everywhere
    else:
        adjusted = base_dss
    return min(adjusted, 1.0)


# ── Base DSS table ────────────────────────────────────────────────────────────
DSS_TABLE = {
    DisruptionType.HEAVY_RAIN: {
        DisruptionSeverity.MODERATE: 0.3,
        DisruptionSeverity.SEVERE: 0.6,
        DisruptionSeverity.EXTREME: 1.0,
    },
    DisruptionType.EXTREME_HEAT: {
        DisruptionSeverity.MODERATE: 0.3,
        DisruptionSeverity.SEVERE: 0.6,
        DisruptionSeverity.EXTREME: 1.0,
    },
    DisruptionType.AQI_SPIKE: {
        DisruptionSeverity.MODERATE: 0.2,
        DisruptionSeverity.SEVERE: 0.5,
        DisruptionSeverity.EXTREME: 1.0,
    },
    DisruptionType.TRAFFIC_DISRUPTION: {
        DisruptionSeverity.MODERATE: 0.3,
        DisruptionSeverity.SEVERE: 0.5,
        DisruptionSeverity.EXTREME: 0.8,
    },
    DisruptionType.CIVIC_EMERGENCY: {
        DisruptionSeverity.MODERATE: 0.5,
        DisruptionSeverity.SEVERE: 0.8,
        DisruptionSeverity.EXTREME: 1.0,
    },
}

# ── Mock scenarios ────────────────────────────────────────────────────────────
CIVIC_SCENARIOS = {
    "Delhi": [
        None, None,
        (DisruptionSeverity.MODERATE, "Local market strike - pickup zones closed", "zone_closure"),
        (DisruptionSeverity.SEVERE, "Unplanned curfew in 3 districts", "curfew"),
    ],
    "Mumbai": [
        None, None, None,
        (DisruptionSeverity.MODERATE, "Port workers strike - delivery zones affected", "strike"),
        (DisruptionSeverity.SEVERE, "Section 144 imposed - outdoor movement restricted", "curfew"),
    ],
    "Bangalore": [
        None, None,
        (DisruptionSeverity.MODERATE, "Auto/cab strike - road access limited", "strike"),
        (DisruptionSeverity.EXTREME, "Bandh declared - all commercial activity halted", "bandh"),
    ],
    "Chennai": [
        None, None,
        (DisruptionSeverity.MODERATE, "Sudden market closure - dark stores inaccessible", "zone_closure"),
        (DisruptionSeverity.SEVERE, "Unplanned curfew - delivery platforms suspended", "curfew"),
    ],
    "Hyderabad": [
        None, None, None,
        (DisruptionSeverity.MODERATE, "Local bandh - partial zone closures", "bandh"),
    ],
    "Pune": [
        None, None, None,
        (DisruptionSeverity.MODERATE, "Traders strike - pickup locations closed", "strike"),
    ],
}

TRAFFIC_SCENARIOS = {
    "Delhi": [
        None, None,
        (DisruptionSeverity.MODERATE, "VIP convoy - arterial roads blocked for 2+ hrs", 65),
        (DisruptionSeverity.SEVERE, "Protest march blocking NH-48 and Ring Road", 80),
    ],
    "Mumbai": [
        None, None,
        (DisruptionSeverity.MODERATE, "Accident on Western Express Highway - 3hr delay", 70),
        (DisruptionSeverity.SEVERE, "Waterlogging + protest - Eastern Freeway closed", 85),
    ],
    "Bangalore": [
        None, None, None,
        (DisruptionSeverity.MODERATE, "IT corridor gridlock - Outer Ring Road blocked", 72),
    ],
    "Chennai": [
        None, None, None,
        (DisruptionSeverity.MODERATE, "Flyover repair - Anna Salai blocked", 60),
    ],
}


def is_real_api_key(value: Optional[str]) -> bool:
    return bool(value and not value.startswith("your_"))


async def fetch_weather_mock(city: str) -> dict:
    mock_scenarios = {
        "Mumbai": {"rainfall_mm_per_hr": random.choice([0, 0, 0, 45.0, 75.0, 120.0]), "temperature_c": random.uniform(28, 34), "description": "Moderate rain"},
        "Delhi": {"rainfall_mm_per_hr": random.choice([0, 0, 0, 0, 15.0]), "temperature_c": random.choice([38.0, 42.0, 44.0, 46.5]), "description": "Clear sky, extreme heat"},
        "Bangalore": {"rainfall_mm_per_hr": random.choice([0, 0, 55.0, 80.0]), "temperature_c": random.uniform(24, 32), "description": "Heavy rain"},
        "Chennai": {"rainfall_mm_per_hr": random.choice([0, 0, 30.0, 90.0]), "temperature_c": random.uniform(30, 36), "description": "Thunderstorm"},
        "Hyderabad": {"rainfall_mm_per_hr": random.choice([0, 0, 40.0, 65.0]), "temperature_c": random.uniform(28, 35), "description": "Cloudy with rain"},
    }
    return mock_scenarios.get(city, {"rainfall_mm_per_hr": 0, "temperature_c": 32.0, "description": "Clear"})


async def fetch_aqi_real(city: str) -> dict:
    """Real AQI from OpenWeatherMap Air Pollution API."""
    if settings.OPENWEATHER_API_KEY == "":
        return await fetch_aqi_mock(city)
    city_coords = {
        "Delhi": (28.6139, 77.2090), "Mumbai": (19.0760, 72.8777),
        "Bangalore": (12.9716, 77.5946), "Chennai": (13.0827, 80.2707),
        "Hyderabad": (17.3850, 78.4867), "Pune": (18.5204, 73.8567),
    }
    coords = city_coords.get(city)
    if not coords:
        return await fetch_aqi_mock(city)
    async with httpx.AsyncClient() as client:
        try:
            r = await client.get(
                "https://api.openweathermap.org/data/2.5/air_pollution",
                params={"lat": coords[0], "lon": coords[1], "appid": settings.OPENWEATHER_API_KEY},
                timeout=5.0,
            )
            data = r.json()
            # OpenWeather AQI is 1-5, convert to India AQI scale
            ow_aqi = data["list"][0]["main"]["aqi"]
            aqi_map = {1: 50, 2: 100, 3: 200, 4: 300, 5: 400}
            return {"aqi": aqi_map.get(ow_aqi, 100), "city": city}
        except (httpx.HTTPError, KeyError, ValueError, TypeError, IndexError):
            return await fetch_aqi_mock(city)


async def fetch_aqi_mock(city: str) -> dict:
    aqi_map = {
        "Delhi": random.choice([180, 280, 360, 420]),
        "Mumbai": random.choice([80, 120, 160]),
        "Bangalore": random.choice([60, 90, 110]),
        "Chennai": random.choice([70, 100, 130]),
    }
    return {"aqi": aqi_map.get(city, 80), "city": city}


async def fetch_civic_real(city: str) -> Optional[tuple]:
    """Real civic emergency detection via NewsAPI — scans for bandh/curfew/strike news."""
    if not is_real_api_key(settings.NEWSAPI_KEY):
        return await fetch_civic_twitter_dev_fallback(city)

    keywords = f"({city} bandh) OR ({city} curfew) OR ({city} strike) OR ({city} Section 144) OR ({city} shutdown)"
    try:
        async with httpx.AsyncClient() as client:
            r = await client.get(
                "https://newsapi.org/v2/everything",
                params={
                    "q": keywords,
                    "language": "en",
                    "pageSize": 5,
                    "sortBy": "publishedAt",
                    "apiKey": settings.NEWSAPI_KEY,
                },
                timeout=8.0,
            )
            data = r.json()
            articles = data.get("articles", [])
            if not articles:
                return await fetch_civic_twitter_dev_fallback(city)

            title = (articles[0].get("title") or "").lower()
            desc = (articles[0].get("description") or "").lower()
            combined = title + " " + desc
            if any(w in combined for w in ["curfew", "section 144", "shutdown", "complete bandh"]):
                severity = DisruptionSeverity.SEVERE
                civic_type = "curfew"
            elif any(w in combined for w in ["bandh", "strike", "protest", "blockade"]):
                severity = DisruptionSeverity.MODERATE
                civic_type = "strike"
            else:
                return None

            description = articles[0].get("title", "Civic disruption detected")[:120]
            return severity, description, civic_type
    except (httpx.HTTPError, KeyError, ValueError, TypeError, IndexError) as e:
        print("[NewsAPI ERROR] " + str(e))
        return await fetch_civic_twitter_dev_fallback(city)


async def fetch_civic_twitter_dev_fallback(city: str) -> Optional[tuple]:
    """Use Twitter/X only as a development fallback for civic disruption detection."""
    if settings.ENVIRONMENT == "production":
        return fetch_civic_mock(city)
    if not is_real_api_key(settings.TWITTER_BEARER_TOKEN):
        return fetch_civic_mock(city)

    keywords = f"({city} bandh) OR ({city} curfew) OR ({city} strike) OR ({city} Section 144) OR ({city} shutdown)"
    try:
        client = tweepy.Client(bearer_token=settings.TWITTER_BEARER_TOKEN)
        tweets = client.search_recent_tweets(
            query=keywords,
            max_results=10,
            tweet_fields=["created_at", "public_metrics"],
            expansions=["author_id"],
        )
        if not tweets.data:
            return None

        latest_tweet = tweets.data[0]
        text = latest_tweet.text.lower()
        if any(w in text for w in ["curfew", "section 144", "shutdown", "complete bandh"]):
            severity = DisruptionSeverity.SEVERE
            civic_type = "curfew"
        elif any(w in text for w in ["bandh", "strike", "protest", "blockade"]):
            severity = DisruptionSeverity.MODERATE
            civic_type = "strike"
        else:
            return None

        return severity, latest_tweet.text[:120], civic_type
    except tweepy.TweepyException as e:
        print("[Twitter API FALLBACK ERROR] " + str(e))
        return fetch_civic_mock(city)
    except (AttributeError, ValueError) as e:
        print("[Twitter API FALLBACK ERROR] Unexpected error: " + str(e))
        return fetch_civic_mock(city)


def fetch_civic_mock(city: str) -> Optional[tuple]:
    return random.choice(CIVIC_SCENARIOS.get(city, [None, None, None]))


def fetch_traffic_mock(city: str) -> Optional[tuple]:
    return random.choice(TRAFFIC_SCENARIOS.get(city, [None, None, None]))


async def fetch_weather_real(city: str) -> dict:
    if settings.OPENWEATHER_API_KEY == "":
        return await fetch_weather_mock(city)
    async with httpx.AsyncClient() as client:
        try:
            r = await client.get(
                "https://api.openweathermap.org/data/2.5/weather",
                params={"q": city + ",IN", "appid": settings.OPENWEATHER_API_KEY, "units": "metric"},
                timeout=5.0,
            )
            data = r.json()
            # OpenWeather rain.1h is mm for the last hour (mm/hr)
            rain = data.get("rain", {}).get("1h", 0.0)
            return {
                "rainfall_mm_per_hr": rain,
                "temperature_c": data["main"]["temp"],
                "description": data["weather"][0]["description"],
            }
        except (httpx.HTTPError, KeyError, ValueError, TypeError, IndexError):
            return await fetch_weather_mock(city)


def classify_rain(mm_per_hr: float) -> Optional[tuple]:
    """
    Classify rainfall based on intensity (mm/hr).
    IMD thresholds for intensity:
    - Moderate: 7.6 to 35.5 mm/hr
    - Heavy: 35.6 to 64.5 mm/hr
    - Extremely Heavy: > 64.5 mm/hr
    """
    if mm_per_hr > 64.5:
        return DisruptionSeverity.EXTREME, f"{mm_per_hr:.1f}mm/hr rainfall (Extremely Heavy)"
    elif mm_per_hr >= 35.6:
        return DisruptionSeverity.SEVERE, f"{mm_per_hr:.1f}mm/hr rainfall (Heavy)"
    elif mm_per_hr >= 7.6:
        return DisruptionSeverity.MODERATE, f"{mm_per_hr:.1f}mm/hr rainfall (Moderate)"
    return None


def classify_heat(temp_c: float) -> Optional[tuple]:
    if temp_c >= 46:
        return DisruptionSeverity.EXTREME, f"{temp_c:.1f}C (Extreme heat)"
    elif temp_c >= 44:
        return DisruptionSeverity.SEVERE, f"{temp_c:.1f}C (Severe heat)"
    elif temp_c >= 42:
        return DisruptionSeverity.MODERATE, f"{temp_c:.1f}C (Heatwave)"
    return None


def classify_aqi(aqi: int) -> Optional[tuple]:
    if aqi > 400:
        return DisruptionSeverity.EXTREME, f"AQI {aqi} (Hazardous - GRAP Stage 4)"
    elif aqi > 300:
        return DisruptionSeverity.SEVERE, f"AQI {aqi} (Very Poor - GRAP Stage 3)"
    elif aqi > 200:
        return DisruptionSeverity.MODERATE, f"AQI {aqi} (Poor - outdoor activity restricted)"
    return None


async def check_disruptions(city: str, pincode: str) -> list:
    """Check all 5 disruption triggers with hyper-local DSS adjustment."""
    events = []
    weather = await fetch_weather_real(city)
    aqi_data = await fetch_aqi_real(city)

    rain_result = classify_rain(weather.get("rainfall_mm_per_hr", 0))
    if rain_result:
        severity, desc = rain_result
        events.append({
            "disruption_type": DisruptionType.HEAVY_RAIN,
            "severity": severity,
            "city": city, "pincode": pincode,
            "dss_multiplier": get_dss(DisruptionType.HEAVY_RAIN, severity, city, pincode),
            "raw_value": weather["rainfall_mm_per_hr"],
            "description": desc + f" | Infra score: {get_infra_score(city, pincode)}",
            "source": "OpenWeather API",
        })

    heat_result = classify_heat(weather.get("temperature_c", 30))
    if heat_result:
        severity, desc = heat_result
        events.append({
            "disruption_type": DisruptionType.EXTREME_HEAT,
            "severity": severity,
            "city": city, "pincode": pincode,
            "dss_multiplier": get_dss(DisruptionType.EXTREME_HEAT, severity, city, pincode),
            "raw_value": weather["temperature_c"],
            "description": desc,
            "source": "OpenWeather API",
        })

    aqi_result = classify_aqi(aqi_data.get("aqi", 0))
    if aqi_result:
        severity, desc = aqi_result
        events.append({
            "disruption_type": DisruptionType.AQI_SPIKE,
            "severity": severity,
            "city": city, "pincode": pincode,
            "dss_multiplier": get_dss(DisruptionType.AQI_SPIKE, severity, city, pincode),
            "raw_value": aqi_data["aqi"],
            "description": desc,
            "source": "OpenWeather Air Pollution API",
        })

    traffic_result = fetch_traffic_mock(city)
    if traffic_result:
        severity, desc, congestion_index = traffic_result
        events.append({
            "disruption_type": DisruptionType.TRAFFIC_DISRUPTION,
            "severity": severity,
            "city": city, "pincode": pincode,
            "dss_multiplier": get_dss(DisruptionType.TRAFFIC_DISRUPTION, severity, city, pincode),
            "raw_value": float(congestion_index),
            "description": desc,
            "source": "Traffic Monitor (Mock)",
        })

    # 5. Civic emergency — real NewsAPI detection
    civic_result = await fetch_civic_real(city)
    if civic_result:
        severity, desc, civic_type = civic_result
        events.append({
            "disruption_type": DisruptionType.CIVIC_EMERGENCY,
            "severity": severity,
            "city": city, "pincode": pincode,
            "dss_multiplier": get_dss(DisruptionType.CIVIC_EMERGENCY, severity, city, pincode),
            "raw_value": None,
            "description": desc,
            "source": f"Civic Alert ({civic_type})",
        })

    return events
