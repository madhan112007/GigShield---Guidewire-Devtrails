import requests

BASE = "http://localhost:8000/api/v1"

print("=== Testing Anitha's account ===\n")

r = requests.post(f"{BASE}/auth/verify-otp", json={"phone": "+911111111111", "otp": "123456"})
d = r.json()
print(f"is_dev_mode : {d['is_dev_mode']}")
TOKEN = d["access_token"]
H = {"Authorization": f"Bearer {TOKEN}"}

me = requests.get(f"{BASE}/workers/me", headers=H).json()
print(f"name        : {me.get('name')}")
print(f"city        : {me.get('city')}")
print(f"pincode     : {me.get('pincode')}")
print(f"platform    : {me.get('platform')}")

pol = requests.get(f"{BASE}/policies/active", headers=H)
if pol.status_code == 200:
    p = pol.json()
    print(f"policy      : {p['tier']} | expires {p['end_date'][:10]}")
    print(f"total_claimed: Rs.{p['total_claimed']} / Rs.{p['max_weekly_payout']}")
else:
    print("No active policy — creating pro")
    requests.post(f"{BASE}/policies/", headers=H, json={"tier": "pro", "pincode": me.get("pincode")})

city = me.get("city")
pincode = me.get("pincode")
print(f"\nSimulating for city={city} pincode={pincode}")

r = requests.post(f"{BASE}/disruptions/simulate?city={city}&pincode={pincode}", headers=H)
events = r.json()
if not isinstance(events, list) or not events:
    print(f"ERROR: {events}")
    exit(1)

event = events[0]
print(f"event_id    : {event['id']}")
print(f"type        : {event['disruption_type']} | {event['severity']}")
print(f"event city  : {event['city']}")

r = requests.post(f"{BASE}/claims/trigger/{event['id']}", headers=H)
claim = r.json()
if "detail" in claim:
    print(f"\nCLAIM ERROR : {claim['detail']}")
else:
    print(f"\nClaim status : {claim.get('status')}")
    print(f"Amount       : Rs.{claim.get('approved_amount')}")
    print(f"Fraud score  : {claim.get('fraud_score')}")
    print(f"hours_ratio  : {claim.get('active_hours_ratio')}")

notifs = requests.get(f"{BASE}/notifications/", headers=H).json()
print(f"\nLatest 3 notifications:")
for n in notifs[:3]:
    print(f"  [{n['type']}] {n['title']} | {n['body'][:50]}")
