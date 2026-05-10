"""
Celery background workers for GigShield
Handles periodic disruption monitoring and auto-claim triggering
"""
from celery import Celery
from celery.schedules import crontab
from app.config import settings

celery_app = Celery(
    "gigshield",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["app.workers.tasks"],
)

celery_app.conf.beat_schedule = {
    # ── Production: daily 3am IST batch settlement ────────────────────────
    # Analyses last 24hrs GPS + disruptions for all workers → settles claims
    # Workers get UPI payout by 6am before they start their day
    "daily-batch-settlement": {
        "task": "app.workers.tasks.daily_batch_settlement",
        "schedule": crontab(hour=21, minute=30),  # 21:30 UTC = 3:00am IST
    },
    # ── Disruption monitoring: every 15 min ───────────────────────────────
    # Stores disruption events in DB for batch to pick up
    "poll-weather": {
        "task": "app.workers.tasks.poll_weather_all_cities",
        "schedule": 900.0,  # 15 min
    },
    # ── AQI monitoring: every 60 min ──────────────────────────────────────
    "poll-aqi": {
        "task": "app.workers.tasks.poll_aqi_all_cities",
        "schedule": 3600.0,
    },
    # ── Policy expiry: daily ──────────────────────────────────────────────
    "expire-policies": {
        "task": "app.workers.tasks.expire_old_policies",
        "schedule": crontab(hour=21, minute=0),  # 21:00 UTC = 2:30am IST
    },
    # ── Premium model auto-retrain: every Sunday 3:30am IST ────────────────
    # Blends real claims from DB with synthetic + real weather risk factors
    # Model improves automatically as real claims accumulate
    "retrain-premium-model": {
        "task": "app.workers.tasks.retrain_premium_model",
        "schedule": crontab(hour=22, minute=0, day_of_week=0),  # Sunday 22:00 UTC = 3:30am IST
    },
    # ── Deleted account purge: daily 3:30am IST ───────────────────────────
    # Permanently removes anonymised worker rows after 30-day grace period
    "purge-deleted-accounts": {
        "task": "app.workers.tasks.purge_deleted_accounts",
        "schedule": crontab(hour=22, minute=0),  # 22:00 UTC = 3:30am IST
    },
    # Auto-investigate PENDING claims with fraud_score >= 30 every 10 min
    "auto-investigate-pending-claims": {
        "task": "app.workers.tasks.auto_investigate_pending_claims",
        "schedule": 600.0,
    },
}

celery_app.conf.timezone = "UTC"
