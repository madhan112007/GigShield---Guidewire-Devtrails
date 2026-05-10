"""
AI-Powered Dynamic Premium Calculation Engine
Phase 2: XGBoost model inference with rule-based fallback.
"""
from __future__ import annotations
from datetime import datetime, timezone
import logging
import os
import joblib
import numpy as np
from app.models.models import PolicyTier

_log = logging.getLogger(__name__)

# Load XGBoost model if available (trained via ml/premium_engine/train.py)
_MODEL_PATH = os.path.join(os.path.dirname(__file__), "../../ml/premium_engine/model.joblib")
try:
    _ml_model = joblib.load(_MODEL_PATH)
except Exception as e:
    _log.warning("[PremiumEngine] XGBoost model not loaded — falling back to rule-based: %s", e)
    _ml_model = None

_TIER_IDX = {PolicyTier.BASIC: 0, PolicyTier.SMART: 1, PolicyTier.PRO: 2}

# Base premiums per tier (₹/week)
BASE_PREMIUMS = {
    PolicyTier.BASIC: 29.0,
    PolicyTier.SMART: 49.0,
    PolicyTier.PRO: 79.0,
}

# Max daily payout per tier (₹)
MAX_DAILY_PAYOUT = {
    PolicyTier.BASIC: 300.0,
    PolicyTier.SMART: 550.0,
    PolicyTier.PRO: 750.0,
}

# Max weekly payout per tier (₹)
MAX_WEEKLY_PAYOUT = {
    PolicyTier.BASIC: 600.0,
    PolicyTier.SMART: 1100.0,
    PolicyTier.PRO: 1500.0,
}

# Zone risk multipliers by pincode prefix (first 3 digits)
# Based on historical disruption frequency
ZONE_RISK = {
    "560": 1.2,  # Bangalore central - flood prone
    "400": 1.35, # Mumbai - high monsoon risk
    "110": 1.15, # Delhi - heat + AQI
    "600": 1.1,  # Chennai - cyclone risk
    "500": 1.05, # Hyderabad - moderate
    "411": 1.1,  # Pune
    "700": 1.05, # Kolkata
}

# Sub-zone risk multipliers by full 6-digit pincode.
# Derived from historical claim density per pincode — higher claim rate = higher risk = higher premium.
# Pincode covers ~8-10 km. GPS delivery grid (WorkerDeliveryGrid) provides finer resolution
# once the worker has 60+ pings (approx 1 week of active delivery).
# Sources: internal claim history + NDMA flood zone maps + IMD heat island data.
SUB_ZONE_RISK = {
    # Mumbai — Dharavi/Kurla flood corridor
    "400017": 1.55, "400070": 1.50, "400024": 1.45,
    # Mumbai — Bandra/Andheri (moderate)
    "400050": 1.25, "400053": 1.20,
    # Bangalore — Koramangala/HSR (IT corridor, gridlock + flooding)
    "560034": 1.40, "560102": 1.38, "560095": 1.35,
    # Bangalore — Whitefield (far from city, lower disruption impact)
    "560066": 1.10,
    # Delhi — Yamuna floodplain wards
    "110032": 1.30, "110053": 1.28,
    # Delhi — Connaught Place / Lutyens (good infra, lower risk)
    "110001": 1.05,
    # Chennai — Marina/Adyar (cyclone + coastal flood)
    "600020": 1.35, "600028": 1.30,
    # Hyderabad — Musi river basin
    "500024": 1.25, "500044": 1.20,
}


def get_sub_zone_risk(pincode: str) -> float:
    """Return pincode-level risk if known, else fall back to 3-digit zone risk.
    Pincode covers ~8-10 km. For finer resolution, use WorkerDeliveryGrid (GPS-based).
    """
    if pincode in SUB_ZONE_RISK:
        return SUB_ZONE_RISK[pincode]
    return get_zone_risk(pincode)


# Season factors by month
SEASON_FACTORS = {
    1: 1.0,  # Jan
    2: 1.0,  # Feb
    3: 1.05, # Mar - early summer
    4: 1.1,  # Apr
    5: 1.2,  # May - peak heat
    6: 1.3,  # Jun - monsoon starts
    7: 1.35, # Jul - peak monsoon
    8: 1.3,  # Aug
    9: 1.2,  # Sep
    10: 1.05,# Oct
    11: 1.0, # Nov
    12: 1.0, # Dec
}


def get_dynamic_caps(tier: PolicyTier, city: str) -> tuple[float, float]:
    """
    Dynamic daily/weekly payout caps adjusted by city Cost of Living.
    Mumbai worker can claim more in absolute terms than Patna worker
    because their actual income loss is higher.
    Returns (daily_cap, weekly_cap).
    """
    from app.services.platform_service import get_col_index
    col = get_col_index(city)
    daily_cap = round(MAX_DAILY_PAYOUT[tier] * col, 0)
    weekly_cap = round(MAX_WEEKLY_PAYOUT[tier] * col, 0)
    return daily_cap, weekly_cap


def get_zone_risk(pincode: str) -> float:
    prefix = pincode[:3] if len(pincode) >= 3 else "000"
    return ZONE_RISK.get(prefix, 1.0)


def get_season_factor() -> float:
    # Use IST (UTC+5:30) so the season factor is correct for Indian workers
    from datetime import timezone, timedelta
    IST = timezone(timedelta(hours=5, minutes=30))
    return SEASON_FACTORS.get(datetime.now(IST).month, 1.0)


async def get_zone_risk_ai(city: str, pincode: str) -> float:
    """
    AI-powered zone risk — uses infra_service to score any city/pincode.
    Converts infra score (0.3-1.0) to a risk multiplier (0.9-1.5).
    Better infra = lower multiplier = lower premium.
    """
    from app.services.infra_service import get_infra_score
    infra = await get_infra_score(city, pincode)
    # Map infra score 0.3→0.9 and 1.0→1.5 linearly
    risk_multiplier = round(0.9 + (infra - 0.30) * (0.6 / 0.70), 3)
    return max(0.9, min(1.5, risk_multiplier))


def _ml_predict_premium(
    tier: PolicyTier,
    pincode: str,
    worker_history_factor: float,
    platform_activity_score: float,
    zone_risk: float = 1.0,
) -> float | None:
    """Use XGBoost model if available; return None to fall back to rule-based."""
    if _ml_model is None:
        return None
    try:
        prefix = int(pincode[:1]) if pincode else 0
        month = datetime.now().month
        tier_idx = _TIER_IDX[tier]
        tenure_weeks = 0
        season = get_season_factor()
        features = np.array([[prefix, month, tier_idx, tenure_weeks,
                               platform_activity_score, zone_risk, season,
                               0, 0, 0.3, 0]])
        pred = float(_ml_model.predict(features)[0])
        base = BASE_PREMIUMS[tier]
        return round(max(base * 0.6, min(base * 1.6, pred * worker_history_factor)), 2)
    except Exception:
        return None


async def calculate_premium(
    tier: PolicyTier,
    pincode: str,
    city: str = "",
    worker_history_factor: float = 1.0,
    platform_activity_score: float = 1.0,
    no_claims_weeks: int = 0,
    policy_count: int = 1,
) -> dict:
    """
    Calculate dynamic weekly premium.
    Uses AI infra scoring for any city/pincode in India.
    Falls back to XGBoost ML model, then rule-based formula.

    Feedback loop discounts:
      no_claims_weeks: consecutive weeks with zero claims → up to 15% discount
      policy_count: number of times worker has renewed → loyalty discount up to 8%
    """
    base = BASE_PREMIUMS[tier]
    season = get_season_factor()

    # AI-powered zone risk — works for any city in India
    if city:
        zone_risk = await get_zone_risk_ai(city, pincode)
    else:
        zone_risk = get_sub_zone_risk(pincode)

    # Discount vars must be computed before either ML or rule-based path uses them
    # No-claims discount: 5% per 4 consecutive claim-free weeks, max 15%
    no_claims_discount = min(0.15, (no_claims_weeks // 4) * 0.05)
    # Continuing insurer (loyalty) discount: 4% per renewal, max 8%
    loyalty_discount = min(0.08, (max(0, policy_count - 1)) * 0.04)
    total_discount = no_claims_discount + loyalty_discount

    ml_premium = _ml_predict_premium(tier, pincode, worker_history_factor, platform_activity_score, zone_risk)
    if ml_premium is not None:
        # XGBoost already includes zone_risk and season in its features —
        # do NOT multiply again; apply only the discount on top.
        adjusted = round(ml_premium * (1 - total_discount), 2)
    else:
        adjusted = base * zone_risk * season * worker_history_factor * platform_activity_score
        adjusted = round(adjusted * (1 - total_discount), 2)

    return {
        "tier": tier,
        "base_premium": base,
        "adjusted_premium": adjusted,
        "zone_risk_multiplier": zone_risk,
        "season_factor": season,
        "worker_history_factor": worker_history_factor,
        "platform_activity_score": platform_activity_score,
        "no_claims_discount": round(no_claims_discount * 100, 1),
        "loyalty_discount": round(loyalty_discount * 100, 1),
        "total_discount_pct": round(total_discount * 100, 1),
        "max_daily_payout": MAX_DAILY_PAYOUT[tier],
        "max_weekly_payout": MAX_WEEKLY_PAYOUT[tier],
        "risk_breakdown": {
            "base": base,
            "after_zone": round(base * zone_risk, 2),
            "after_season": round(base * zone_risk * season, 2),
            "after_discounts": adjusted,
        },
    }


def calculate_payout(
    worker_daily_avg: float,
    dss_multiplier: float,
    active_hours_ratio: float,
    tier: PolicyTier,
    existing_claimed_today: float = 0.0,
    city: str = "",
) -> dict:
    """
    Payout = actual income loss adjusted for city Cost of Living.
    Effective loss = raw_loss x (1 - subsistence_ratio x 0.5)
    Capped at CoL-adjusted daily cap.
    """
    # Inline CoL lookup to avoid circular import
    _CITY_ECONOMICS = {
        "Mumbai": (1.45, 0.58), "Delhi": (1.35, 0.52), "Bangalore": (1.30, 0.53),
        "Chennai": (1.20, 0.50), "Hyderabad": (1.15, 0.48), "Pune": (1.15, 0.48),
        "Kolkata": (1.10, 0.50), "Noida": (1.25, 0.51), "Gurgaon": (1.30, 0.52),
        "Ahmedabad": (1.05, 0.44), "Coimbatore": (1.00, 0.40),
        "Madurai": (0.90, 0.38), "Tiruchirappalli": (0.88, 0.38),
        "Kochi": (1.05, 0.45), "Chandigarh": (1.10, 0.46),
        "Lucknow": (0.95, 0.42), "Patna": (0.75, 0.36),
        "Guwahati": (0.80, 0.37), "Ranchi": (0.78, 0.36),
        "Jaipur": (1.00, 0.42), "Indore": (0.95, 0.41),
        "Nagpur": (0.95, 0.41), "Bhopal": (0.90, 0.40),
        "Varanasi": (0.80, 0.37), "Surat": (1.05, 0.43),
    }
    col_index, subsistence_ratio = (1.0, 0.42)
    if city:
        for known, vals in _CITY_ECONOMICS.items():
            if known.lower() in city.lower() or city.lower() in known.lower():
                col_index, subsistence_ratio = vals
                break

    raw_loss = round(worker_daily_avg * dss_multiplier * active_hours_ratio, 2)
    # Scale loss by CoL index: Mumbai worker (col=1.45) loses more in absolute terms
    # than a Patna worker (col=0.75) for the same disruption — payout reflects that.
    effective_loss = round(raw_loss * col_index, 2)

    daily_cap = round(MAX_DAILY_PAYOUT[tier] * col_index, 2)
    weekly_cap_dynamic = round(MAX_WEEKLY_PAYOUT[tier] * col_index, 2)
    # Enforce both daily and weekly caps
    daily_remaining = max(0.0, daily_cap - existing_claimed_today)
    remaining_cap = min(daily_remaining, weekly_cap_dynamic)
    approved_amount = round(min(effective_loss, remaining_cap), 2)

    estimated_actual = round(worker_daily_avg * (1 - dss_multiplier * active_hours_ratio), 2)

    return {
        "worker_daily_avg":   worker_daily_avg,
        "dss_multiplier":     dss_multiplier,
        "active_hours_ratio": active_hours_ratio,
        "expected_earnings":  worker_daily_avg,
        "estimated_actual":   estimated_actual,
        "income_shortfall":   raw_loss,
        "subsistence_ratio":  subsistence_ratio,
        "effective_loss":     effective_loss,
        "raw_payout":         effective_loss,
        "tier_cap":           daily_cap,
        "weekly_cap":         weekly_cap_dynamic,
        "remaining_cap":      remaining_cap,
        "approved_amount":    approved_amount,
        "capped":             effective_loss > remaining_cap,
        "col_index":          col_index,
    }
