import requests

BASE = "http://localhost:8000/api/v1"

# Fresh worker
r = requests.post(f"{BASE}/auth/verify-otp", json={"phone": "+919111111111", "otp": "123456"})
TOKEN = r.json()["access_token"]
H = {"Authorization": f"Bearer {TOKEN}"}

# Policy
requests.post(f"{BASE}/policies/", headers=H, json={"tier": "smart", "pincode": "400001"})

# Fresh simulate
r = requests.post(f"{BASE}/disruptions/simulate?city=Mumbai&pincode=400001", headers=H)
events = r.json()
event_id = events[0]["id"]
print(f"Event     : {event_id}")
print(f"DSS       : {events[0]['dss_multiplier']}")
print(f"started_at: {events[0]['started_at']}")

# Trigger claim
r = requests.post(f"{BASE}/claims/trigger/{event_id}", headers=H)
claim = r.json()
print(f"\nClaim status    : {claim.get('status')}")
print(f"approved_amount : Rs.{claim.get('approved_amount')}")
print(f"hours_ratio     : {claim.get('active_hours_ratio')}")
print(f"dss_multiplier  : {claim.get('dss_multiplier')}")
print(f"worker_daily_avg: Rs.{claim.get('worker_daily_avg')}")

# Manual check
d = claim.get("worker_daily_avg", 0)
dss = claim.get("dss_multiplier", 0)
hrs = claim.get("active_hours_ratio", 0)
print(f"\nManual: {d} x {dss} x {hrs} = Rs.{round(d*dss*hrs, 2)}")

# Notifications
notifs = requests.get(f"{BASE}/notifications/", headers=H).json()
print("\nNotifications:")
for n in notifs[:4]:
    print(f"  [{n['type']}] {n['title']} | {n['body'][:50]}")
