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
}

celery_app.conf.timezone = "Asia/Kolkata"
