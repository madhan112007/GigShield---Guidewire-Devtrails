"""
Geocoding Service — PositionStack forward geocoding.
Resolves city name → (pincode, lat, lng) for any Indian city.
Primary: PositionStack API.
Fallback: hardcoded pincode map (covers all cities in CITY_ECONOMICS).
Results are cached in-memory so the API is hit only once per city per process boot.
"""
import httpx
from app.config import settings

_cache: dict[str, tuple[str, float, float]] = {}

# Fallback pincode map — used when PositionStack is unavailable or returns no result.
# Covers every city in platform_service.CITY_ECONOMICS.
_FALLBACK_PINCODES: dict[str, str] = {
    "Mumbai": "400001", "Delhi": "110001", "Bangalore": "560001",
    "Chennai": "600001", "Hyderabad": "500001", "Pune": "411001",
    "Kolkata": "700001", "Noida": "201301", "Gurgaon": "122001",
    "Ahmedabad": "380001", "Surat": "395001", "Jaipur": "302001",
    "Lucknow": "226001", "Indore": "452001", "Bhopal": "462001",
    "Nagpur": "440001", "Coimbatore": "641001", "Madurai": "625001",
    "Tiruchirappalli": "620001", "Kochi": "682001", "Chandigarh": "160001",
    "Visakhapatnam": "530001", "Vadodara": "390001", "Amritsar": "143001",
    "Ludhiana": "141001", "Patna": "800001", "Guwahati": "781001",
    "Ranchi": "834001", "Varanasi": "221001", "Agra": "282001",
    "Meerut": "250001", "Gorakhpur": "273001", "Siliguri": "734001",
}


async def resolve_city(city: str) -> tuple[str, float, float]:
    """
    Returns (pincode, lat, lng) for a given Indian city name.
    Primary: PositionStack API.
    Fallback: _FALLBACK_PINCODES hardcoded map.
    Last resort: ("000000", 0.0, 0.0) — city will be skipped by the caller.
    """
    if city in _cache:
        return _cache[city]

    pincode, lat, lng = "", 0.0, 0.0

    # Primary: PositionStack
    if settings.POSITIONSTACK_API_KEY and not settings.POSITIONSTACK_API_KEY.startswith("your_"):
        try:
            async with httpx.AsyncClient(timeout=8.0) as client:
                r = await client.get(
                    "http://api.positionstack.com/v1/forward",
                    params={
                        "access_key": settings.POSITIONSTACK_API_KEY,
                        "query": f"{city}, India",
                        "country": "IN",
                        "limit": 1,
                        "fields": "results.latitude,results.longitude,results.postal_code",
                    },
                )
                result = (r.json().get("data") or [])[0]
                pincode = (result.get("postal_code") or "").replace(" ", "")[:6]
                lat = float(result.get("latitude") or 0.0)
                lng = float(result.get("longitude") or 0.0)
        except Exception as e:
            print(f"[Geocoding] PositionStack failed for {city}: {e} — using fallback")

    # Fallback: hardcoded map
    if not pincode:
        pincode = _FALLBACK_PINCODES.get(city, "000000")
        if pincode != "000000":
            print(f"[Geocoding] Using hardcoded fallback pincode for {city}: {pincode}")

    _cache[city] = (pincode, lat, lng)
    return pincode, lat, lng


async def resolve_all_cities(cities: list[str]) -> dict[str, tuple[str, float, float]]:
    """Resolve a list of city names concurrently. Returns {city: (pincode, lat, lng)}."""
    import asyncio
    results = await asyncio.gather(*[resolve_city(c) for c in cities])
    return dict(zip(cities, results))
