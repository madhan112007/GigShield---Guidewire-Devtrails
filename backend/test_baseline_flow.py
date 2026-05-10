import requests

BASE = "http://localhost:8000/api/v1"

# Fresh worker
r = requests.post(f"{BASE}/auth/verify-otp", json={"phone": "+919222222222", "otp": "123456"})
TOKEN = r.json()["access_token"]
H = {"Authorization": f"Bearer {TOKEN}"}

# Register with self-reported work pattern
requests.post(f"{BASE}/workers/register", headers=H, json={
    "name": "Test Blinkit Worker",
    "platform": "blinkit",
    "city": "Mumbai",
    "pincode": "400001",
    "avg_online_hours_per_day": 9.5,
    "avg_orders_per_day": 24.0,
})

# Check worker profile
me = requests.get(f"{BASE}/workers/me", headers=H).json()
print("=== WORKER PROFILE ===")
print(f"platform          : {me.get('platform')}")
print(f"city              : {me.get('city')}")
print(f"avg_daily_earnings: Rs.{me.get('avg_daily_earnings')}")
print(f"avg_online_hours  : {me.get('avg_online_hours_per_day')} hrs/day")
print(f"avg_orders/day    : {me.get('avg_orders_per_day')} orders")

# Derived baseline (what claims engine will use)
daily = me.get("avg_daily_earnings", 600)
online_hrs = me.get("avg_online_hours_per_day", 9.0)
orders = me.get("avg_orders_per_day", 18.0)
hourly = round(daily / online_hrs, 2)
orders_per_hr = round(orders / online_hrs, 2)
print(f"\n=== COMPUTED BASELINE ===")
print(f"avg_hourly_earnings : Rs.{hourly}/hr")
print(f"avg_orders_per_hour : {orders_per_hr} orders/hr")

# Policy + simulate + claim
requests.post(f"{BASE}/policies/", headers=H, json={"tier": "smart", "pincode": "400001"})
events = requests.post(f"{BASE}/disruptions/simulate?city=Mumbai&pincode=400001", headers=H).json()
event_id = events[0]["id"]
print(f"\n=== DISRUPTION EVENT ===")
print(f"event_id  : {event_id}")
print(f"type      : {events[0]['disruption_type']}")
print(f"severity  : {events[0]['severity']}")
print(f"dss       : {events[0]['dss_multiplier']}")

claim = requests.post(f"{BASE}/claims/trigger/{event_id}", headers=H).json()
print(f"\n=== CLAIM RESULT ===")
print(f"status          : {claim.get('status')}")
print(f"approved_amount : Rs.{claim.get('approved_amount')}")
print(f"hours_ratio     : {claim.get('active_hours_ratio')}")
print(f"dss_multiplier  : {claim.get('dss_multiplier')}")

# Show order drop rate used
from_ORDER_DROP = {
    "heavy_rain": {"moderate": 0.20, "severe": 0.45, "extreme": 0.75},
}
drop = from_ORDER_DROP.get(events[0]["disruption_type"], {}).get(events[0]["severity"], 0.30)
print(f"\n=== INCOME LOSS BREAKDOWN ===")
print(f"order_drop_rate   : {drop*100:.0f}% (severe heavy_rain)")
print(f"normal_hourly     : Rs.{hourly}/hr")
print(f"disruption_hours  : ~{claim.get('active_hours_ratio', 0.1) * 16:.1f}h (infra-based)")
print(f"income_loss_ratio : {drop}")
print(f"payout formula    : {daily} x {claim.get('dss_multiplier')} x {claim.get('active_hours_ratio')} x {drop} = Rs.{round(daily * (claim.get('dss_multiplier') or 0) * (claim.get('active_hours_ratio') or 0) * drop, 2)}")
print(f"actual payout     : Rs.{claim.get('approved_amount')}")
