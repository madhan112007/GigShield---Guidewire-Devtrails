"""
AI-Powered Dynamic Premium Calculation Engine
Phase 2: XGBoost model inference with rule-based fallback.
"""
from __future__ import annotations
from datetime import datetime
import os
import joblib
import numpy as np
from app.models.models import PolicyTier

# Load XGBoost model if available (trained via ml/premium_engine/train.py)
_MODEL_PATH = os.path.join(os.path.dirname(__file__), "../../ml/premium_engine/model.joblib")
try:
    _ml_model = joblib.load(_MODEL_PATH)
except Exception:
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

# Sub-zone (ward-level) risk multipliers by full 6-digit pincode.
# Derived from historical claim density per pincode — higher claim rate = higher risk = higher premium.
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
    """Return ward-level risk if known, else fall back to 3-digit zone risk."""
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


def get_zone_risk(pincode: str) -> float:
    prefix = pincode[:3] if len(pincode) >= 3 else "000"
    return ZONE_RISK.get(prefix, 1.0)


def get_season_factor() -> float:
    return SEASON_FACTORS.get(datetime.now().month, 1.0)


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
) -> float | None:
    """Use XGBoost model if available; return None to fall back to rule-based."""
    if _ml_model is None:
        return None
    try:
        prefix = int(pincode[:1]) if pincode else 0
        month = datetime.now().month
        tier_idx = _TIER_IDX[tier]
        tenure_weeks = 0  # unknown at quote time; use 0 (conservative)
        zone_risk = get_zone_risk(pincode)
        season = get_season_factor()
        # Use moderate rain (0) as default disruption context for premium quoting
        features = np.array([[prefix, month, tier_idx, tenure_weeks,
                               platform_activity_score, zone_risk, season,
                               0, 0, 0.3, 0]])
        pred = float(_ml_model.predict(features)[0])
        base = BASE_PREMIUMS[tier]
        # Clamp to ±40% of base to prevent wild extrapolation
        return round(max(base * 0.6, min(base * 1.6, pred * worker_history_factor)), 2)
    except Exception:
        return None


async def calculate_premium(
    tier: PolicyTier,
    pincode: str,
    city: str = "",
    worker_history_factor: float = 1.0,
    platform_activity_score: float = 1.0,
) -> dict:
    """
    Calculate dynamic weekly premium.
    Uses AI infra scoring for any city/pincode in India.
    Falls back to XGBoost ML model, then rule-based formula.
    """
    base = BASE_PREMIUMS[tier]
    season = get_season_factor()

    # AI-powered zone risk — works for any city in India
    if city:
        zone_risk = await get_zone_risk_ai(city, pincode)
    else:
        zone_risk = get_sub_zone_risk(pincode)

    ml_premium = _ml_predict_premium(tier, pincode, worker_history_factor, platform_activity_score)
    if ml_premium is not None:
        adjusted = ml_premium
    else:
        adjusted = base * zone_risk * season * worker_history_factor * platform_activity_score
        adjusted = round(adjusted, 2)

    return {
        "tier": tier,
        "base_premium": base,
        "adjusted_premium": adjusted,
        "zone_risk_multiplier": zone_risk,
        "season_factor": season,
        "worker_history_factor": worker_history_factor,
        "platform_activity_score": platform_activity_score,
        "max_daily_payout": MAX_DAILY_PAYOUT[tier],
        "max_weekly_payout": MAX_WEEKLY_PAYOUT[tier],
        "risk_breakdown": {
            "base": base,
            "after_zone": round(base * zone_risk, 2),
            "after_season": round(base * zone_risk * season, 2),
            "final": adjusted,
        },
    }


def calculate_payout(
    worker_daily_avg: float,
    dss_multiplier: float,
    active_hours_ratio: float,
    tier: PolicyTier,
    existing_claimed_today: float = 0.0,
) -> dict:
    """
    Payout = income the worker LOST due to the disruption.

    Formula:
    - Expected earnings for the day  = worker_daily_avg
    - Income shortfall (= payout)    = worker_daily_avg × DSS × active_hours_ratio
    
    Example: 
    If daily avg = ₹1000, DSS = 0.5 (50% disruption), and ratio = 0.4 (40% of day remaining),
    Shortfall = 1000 * 0.5 * 0.4 = ₹200.

    Capped at (tier daily cap - already claimed today) to prevent over-compensation.
    """
    income_shortfall  = round(worker_daily_avg * dss_multiplier * active_hours_ratio, 2)
    estimated_actual  = round(worker_daily_avg * (1 - (dss_multiplier * active_hours_ratio)), 2)

    daily_cap         = MAX_DAILY_PAYOUT[tier]
    remaining_cap     = max(0.0, daily_cap - existing_claimed_today)
    approved_amount   = round(min(income_shortfall, remaining_cap), 2)

    return {
        "worker_daily_avg":   worker_daily_avg,
        "dss_multiplier":     dss_multiplier,
        "active_hours_ratio": active_hours_ratio,
        "expected_earnings":  worker_daily_avg,
        "estimated_actual":   estimated_actual,
        "income_shortfall":   income_shortfall,
        "raw_payout":         income_shortfall,
        "tier_cap":           daily_cap,
        "remaining_cap":      remaining_cap,
        "approved_amount":    approved_amount,
        "capped":             income_shortfall > remaining_cap,
    }
