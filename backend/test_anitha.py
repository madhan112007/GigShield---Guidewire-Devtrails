import requests

BASE = "http://localhost:8000/api/v1"

# Login as Anitha (use her actual phone)
print("=== Testing Anitha's simulate flow ===\n")

# Get fresh token with dev OTP
r = requests.post(f"{BASE}/auth/send-otp", json={"phone": "+919876543210"})
r = requests.post(f"{BASE}/auth/verify-otp", json={"phone": "+919876543210", "otp": "123456"})
d = r.json()
print(f"is_dev_mode: {d['is_dev_mode']}")
TOKEN = d["access_token"]
H = {"Authorization": f"Bearer {TOKEN}"}

# Check worker
me = requests.get(f"{BASE}/workers/me", headers=H).json()
print(f"worker city : {me.get('city')}")
print(f"worker name : {me.get('name')}")

# Check active policy
pol = requests.get(f"{BASE}/policies/active", headers=H)
if pol.status_code == 200:
    p = pol.json()
    print(f"policy      : {p['tier']} | expires {p['end_date'][:10]}")
    print(f"total_claimed: Rs.{p['total_claimed']} / Rs.{p['max_weekly_payout']}")
else:
    print(f"policy      : NONE - creating one")
    requests.post(f"{BASE}/policies/", headers=H, json={"tier": "pro", "pincode": me.get("pincode", "621211")})

# Simulate
city = me.get("city", "Tiruchchirappalli")
pincode = me.get("pincode", "621211")
print(f"\nSimulating for city={city} pincode={pincode}")
r = requests.post(f"{BASE}/disruptions/simulate?city={city}&pincode={pincode}", headers=H)
events = r.json()
if isinstance(events, list) and events:
    event = events[0]
    print(f"event_id    : {event['id']}")
    print(f"type        : {event['disruption_type']} | {event['severity']}")
    print(f"city        : {event['city']}")
else:
    print(f"ERROR: {events}")
    exit(1)

# Trigger claim
event_id = events[0]["id"]
r = requests.post(f"{BASE}/claims/trigger/{event_id}", headers=H)
claim = r.json()
if "detail" in claim:
    print(f"\nCLAIM ERROR: {claim['detail']}")
else:
    print(f"\nClaim status : {claim.get('status')}")
    print(f"Amount       : Rs.{claim.get('approved_amount')}")
    print(f"Fraud score  : {claim.get('fraud_score')}")

# Notifications
notifs = requests.get(f"{BASE}/notifications/", headers=H).json()
print(f"\nLatest notifications:")
for n in notifs[:3]:
    print(f"  [{n['type']}] {n['title']}")
