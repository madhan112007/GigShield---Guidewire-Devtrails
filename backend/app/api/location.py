"""
Worker Location Tracking API
- Accepts GPS ping every 10 min from Flutter app during active hours
- Detects GPS spoofing via impossible movement speed (>200 km/h)
- Stores location history for fraud cross-check during claims
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from datetime import datetime, timezone
from math import radians, sin, cos, sqrt, atan2
from app.database import get_db
from app.models.models import Worker, WorkerLocationPing
from app.services.auth_service import get_current_worker

router = APIRouter()

# Max realistic speed for a delivery worker (km/h)
# Bike: ~60 km/h, Car: ~120 km/h — anything >200 = GPS spoof
MAX_REALISTIC_SPEED_KMH = 200.0


class LocationPing(BaseModel):
    lat: float
    lng: float
    accuracy: float = 0.0


def _haversine_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Calculate distance in km between two GPS coordinates."""
    R = 6371.0
    dlat = radians(lat2 - lat1)
    dlng = radians(lng2 - lng1)
    a = sin(dlat/2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlng/2)**2
    return R * 2 * atan2(sqrt(a), sqrt(1 - a))


def _detect_city(lat: float, lng: float) -> tuple:
    """Rough city detection from coordinates."""
    city_bounds = {
        "Delhi":     (28.4, 28.9, 76.8, 77.4),
        "Mumbai":    (18.9, 19.3, 72.7, 73.0),
        "Bangalore": (12.8, 13.2, 77.4, 77.8),
        "Chennai":   (12.9, 13.2, 80.1, 80.4),
        "Hyderabad": (17.2, 17.6, 78.3, 78.7),
        "Pune":      (18.4, 18.7, 73.7, 74.0),
        "Kolkata":   (22.4, 22.7, 88.2, 88.5),
    }
    for city, (lat_min, lat_max, lng_min, lng_max) in city_bounds.items():
        if lat_min <= lat <= lat_max and lng_min <= lng <= lng_max:
            return city, ""
    return "", ""


@router.post("/ping")
async def location_ping(
    payload: LocationPing,
    db: AsyncSession = Depends(get_db),
    current_worker: Worker = Depends(get_current_worker),
):
    """
    Receive GPS ping from worker app every 10 minutes during active hours.
    Detects GPS spoofing via impossible movement speed.
    """
    now = datetime.now(timezone.utc)

    # Get last ping to calculate speed
    last_result = await db.execute(
        select(WorkerLocationPing)
        .where(WorkerLocationPing.worker_id == current_worker.id)
        .order_by(WorkerLocationPing.recorded_at.desc())
        .limit(1)
    )
    last_ping = last_result.scalar_one_or_none()

    distance_km = None
    speed_kmh = None
    is_suspicious = False

    if last_ping:
        last_at = last_ping.recorded_at
        if last_at.tzinfo is None:
            last_at = last_at.replace(tzinfo=timezone.utc)
        time_diff_hours = max((now - last_at).total_seconds() / 3600, 0.001)
        distance_km = round(_haversine_km(last_ping.lat, last_ping.lng, payload.lat, payload.lng), 3)
        speed_kmh = round(distance_km / time_diff_hours, 1)

        # Flag as suspicious if movement is physically impossible
        if speed_kmh > MAX_REALISTIC_SPEED_KMH:
            is_suspicious = True

    city_detected, pincode_detected = _detect_city(payload.lat, payload.lng)

    ping = WorkerLocationPing(
        worker_id=current_worker.id,
        lat=payload.lat,
        lng=payload.lng,
        accuracy=payload.accuracy,
        speed_kmh=speed_kmh,
        distance_km=distance_km,
        is_suspicious=is_suspicious,
        city_detected=city_detected or current_worker.city,
        pincode_detected=pincode_detected or current_worker.pincode,
    )
    db.add(ping)

    # Update worker's last known location
    current_worker.last_known_lat = payload.lat
    current_worker.last_known_lng = payload.lng
    current_worker.last_location_at = now

    await db.commit()

    return {
        "status": "recorded",
        "city_detected": city_detected or current_worker.city,
        "distance_km": distance_km,
        "speed_kmh": speed_kmh,
        "is_suspicious": is_suspicious,
        "message": "GPS spoof detected — flagged for review" if is_suspicious else "Location recorded",
    }


@router.get("/weather")
async def get_weather_by_location(
    lat: float,
    lon: float,
    current_worker: Worker = Depends(get_current_worker),
):
    """
    Fetch live weather + AQI for given lat/lon using OpenWeatherMap.
    Called from Flutter Live Risk screen using the worker's GPS coordinates.
    """
    import httpx
    from app.config import settings

    api_key = settings.OPENWEATHER_API_KEY
    result = {"lat": lat, "lon": lon}

    async with httpx.AsyncClient(timeout=8.0) as client:
        # Current weather by coordinates
        try:
            wr = await client.get(
                "https://api.openweathermap.org/data/2.5/weather",
                params={"lat": lat, "lon": lon, "appid": api_key, "units": "metric"},
            )
            wd = wr.json()
            result["temperature_c"] = wd["main"]["temp"]
            result["feels_like_c"] = wd["main"]["feels_like"]
            result["humidity"] = wd["main"]["humidity"]
            result["wind_kmh"] = round(wd["wind"]["speed"] * 3.6, 1)
            result["description"] = wd["weather"][0]["description"].title()
            result["icon"] = wd["weather"][0]["icon"]
            result["city_name"] = wd.get("name", "")
            result["rainfall_mm_per_hr"] = wd.get("rain", {}).get("1h", 0.0)
            result["visibility_km"] = round(wd.get("visibility", 10000) / 1000, 1)
        except (httpx.HTTPError, KeyError, ValueError, TypeError, IndexError) as e:
            result["weather_error"] = str(e)

        # AQI by coordinates
        try:
            ar = await client.get(
                "https://api.openweathermap.org/data/2.5/air_pollution",
                params={"lat": lat, "lon": lon, "appid": api_key},
            )
            ad = ar.json()
            ow_aqi = ad["list"][0]["main"]["aqi"]
            components = ad["list"][0]["components"]
            # Convert OpenWeather 1-5 AQI to India AQI scale
            aqi_map = {1: 50, 2: 100, 3: 200, 4: 300, 5: 400}
            result["aqi"] = aqi_map.get(ow_aqi, 100)
            result["aqi_level"] = ow_aqi
            result["pm2_5"] = round(components.get("pm2_5", 0), 1)
            result["pm10"] = round(components.get("pm10", 0), 1)
            result["no2"] = round(components.get("no2", 0), 1)
            result["co"] = round(components.get("co", 0), 1)
        except (httpx.HTTPError, KeyError, ValueError, TypeError, IndexError) as e:
            result["aqi_error"] = str(e)

    return result


@router.get("/history")
async def location_history(
    db: AsyncSession = Depends(get_db),
    current_worker: Worker = Depends(get_current_worker),
):
    """Get last 20 location pings for the worker."""
    result = await db.execute(
        select(WorkerLocationPing)
        .where(WorkerLocationPing.worker_id == current_worker.id)
        .order_by(WorkerLocationPing.recorded_at.desc())
        .limit(20)
    )
    pings = result.scalars().all()
    return [
        {
            "lat": p.lat,
            "lng": p.lng,
            "city": p.city_detected,
            "speed_kmh": p.speed_kmh,
            "is_suspicious": p.is_suspicious,
            "recorded_at": p.recorded_at,
        }
        for p in pings
    ]
