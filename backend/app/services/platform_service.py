"""
Platform Earnings Service — Mock (Phase 1)

Simulates what a real platform partner API would return when queried
by a delivery worker's registered phone number.

Real integration (Phase 2):
  - Blinkit  : GET https://partner-api.blinkit.com/v1/earnings?phone={phone}
  - Zepto    : GET https://partner.zepto.co/api/earnings?phone={phone}
  - Swiggy   : GET https://partner.swiggy.com/api/v1/worker/earnings?phone={phone}
  - Zomato   : GET https://hyperpure.zomato.com/partner/api/earnings?phone={phone}
  - Amazon   : GET https://flex.amazon.in/api/earnings?phone={phone}
  - BigBasket: GET https://partner.bigbasket.com/api/earnings?phone={phone}

Each platform returns a weekly settlement summary from which we derive
avg_daily_earnings = weekly_settlement / active_days_in_week.

Per README persona (Arun Kumar, quick-commerce grocery delivery):
  Earnings: ₹800–₹1,200/day  |  ₹5,600–₹8,400/week
"""
import random
import asyncio
from typing import Optional


# Cost of Living index AND subsistence ratio per city
# col_index: relative cost of living (1.0 = Tier-2 base)
# subsistence_ratio: minimum daily spend / typical daily earnings
#   Higher ratio = more of income goes to survival = disruption hurts more relatively
CITY_ECONOMICS = {
    # city: (col_index, subsistence_ratio)
    "Mumbai":          (1.45, 0.58),
    "Delhi":           (1.35, 0.52),
    "Bangalore":       (1.30, 0.53),
    "Chennai":         (1.20, 0.50),
    "Hyderabad":       (1.15, 0.48),
    "Pune":            (1.15, 0.48),
    "Kolkata":         (1.10, 0.50),
    "Noida":           (1.25, 0.51),
    "Gurgaon":         (1.30, 0.52),
    "Ahmedabad":       (1.05, 0.44),
    "Surat":           (1.05, 0.43),
    "Jaipur":          (1.00, 0.42),
    "Lucknow":         (0.95, 0.42),
    "Indore":          (0.95, 0.41),
    "Bhopal":          (0.90, 0.40),
    "Nagpur":          (0.95, 0.41),
    "Coimbatore":      (1.00, 0.40),
    "Madurai":         (0.90, 0.38),
    "Tiruchirappalli": (0.88, 0.38),
    "Kochi":           (1.05, 0.45),
    "Chandigarh":      (1.10, 0.46),
    "Visakhapatnam":   (0.95, 0.41),
    "Vadodara":        (0.95, 0.41),
    "Amritsar":        (0.90, 0.40),
    "Ludhiana":        (0.92, 0.40),
    "Patna":           (0.75, 0.36),
    "Guwahati":        (0.80, 0.37),
    "Ranchi":          (0.78, 0.36),
    "Varanasi":        (0.80, 0.37),
    "Agra":            (0.82, 0.38),
    "Meerut":          (0.85, 0.38),
    "Gorakhpur":       (0.75, 0.35),
    "Siliguri":        (0.80, 0.37),
}

DEFAULT_COL = 1.0
DEFAULT_SUBSISTENCE = 0.42


def get_city_economics(city: str) -> tuple[float, float]:
    """Returns (col_index, subsistence_ratio) for a city."""
    for known, vals in CITY_ECONOMICS.items():
        if known.lower() in city.lower() or city.lower() in known.lower():
            return vals
    return DEFAULT_COL, DEFAULT_SUBSISTENCE


def get_col_index(city: str) -> float:
    return get_city_economics(city)[0]


# Realistic daily earnings ranges per platform (min, max) in ₹
# Based on Tier-2 city average — multiplied by CoL index at runtime
PLATFORM_EARNINGS = {
    "blinkit": {
        "range": (850, 1200),   # 10-min delivery, high order density
        "active_days": (5, 7),
        "label": "Blinkit",
    },
    "zepto": {
        "range": (800, 1150),   # Similar to Blinkit
        "active_days": (5, 7),
        "label": "Zepto",
    },
    "swiggy_instamart": {
        "range": (780, 1100),   # Instamart grocery delivery
        "active_days": (5, 6),
        "label": "Swiggy Instamart",
    },
    "zomato": {
        "range": (700, 1050),   # Food delivery, peak hours dependent
        "active_days": (5, 7),
        "label": "Zomato",
    },
    "amazon": {
        "range": (750, 1000),   # Amazon Flex, scheduled blocks
        "active_days": (4, 6),
        "label": "Amazon",
    },
    "bigbasket": {
        "range": (650, 950),    # Scheduled grocery delivery, lower density
        "active_days": (5, 6),
        "label": "BigBasket",
    },
}

DEFAULT_EARNINGS = 700.0


async def fetch_platform_earnings(phone: str, platform: str, city: str = "") -> dict:
    """
    Mock platform API call — returns avg daily earnings for a worker.
    Earnings are adjusted by city Cost of Living index.
    Mumbai Blinkit rider earns ~45% more than Jaipur Blinkit rider.
    """
    await asyncio.sleep(0.3)

    config = PLATFORM_EARNINGS.get(platform)
    col = get_col_index(city) if city else DEFAULT_COL

    if not config:
        base = round(DEFAULT_EARNINGS * col, 2)
        return {
            "platform": platform,
            "phone": phone,
            "city": city,
            "avg_daily_earnings": base,
            "weekly_settlement": round(base * 6, 2),
            "active_days_last_week": 6,
            "col_index": col,
            "source": "default",
            "verified": False,
        }

    seed = int("".join(filter(str.isdigit, phone))[-6:] or "123456")
    rng = random.Random(seed + hash(platform) % 10000)

    low, high = config["range"]
    # Apply CoL multiplier to earnings range
    avg_daily = round(rng.uniform(low, high) * col, 2)

    day_low, day_high = config["active_days"]
    active_days_week = rng.randint(day_low, day_high)
    active_days_30 = rng.randint(active_days_week * 3, active_days_week * 4)
    weekly_settlement = round(avg_daily * active_days_week, 2)

    return {
        "platform": platform,
        "platform_label": config["label"],
        "phone": phone,
        "city": city,
        "avg_daily_earnings": avg_daily,
        "weekly_settlement": weekly_settlement,
        "active_days_last_week": active_days_week,
        "active_days_30": active_days_30,
        "col_index": col,
        "source": f"{config['label']} Partner API (mock)",
        "verified": True,
    }
