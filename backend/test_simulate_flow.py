re import requests
import json
import sys

BASE = "http://localhost:8000/api/v1"

# Step 1: Login
print("\n=== STEP 1: Login (dev OTP) ===")
r = requests.post(f"{BASE}/auth/verify-otp", json={"phone": "+919000000001", "otp": "123456"})
data = r.json()
TOKEN = data["access_token"]
WORKER_ID = data["worker_id"]
print(f"worker_id : {WORKER_ID}")
print(f"is_dev_mode: {data['is_dev_mode']}")

H = {"Authorization": f"Bearer {TOKEN}"}

# Step 2: Mark all existing notifications read so we only see new ones
print("\n=== STEP 2: Clear existing notifications ===")
requests.post(f"{BASE}/notifications/read-all", headers=H)
print("Cleared.")

# Step 3: Create policy (dev mode)
print("\n=== STEP 3: Create policy (Smart tier) ===")
r = requests.post(f"{BASE}/policies/", headers=H, json={"tier": "smart", "pincode": "400001"})
policy = r.json()
print(f"policy_id : {policy.get('id')}")
print(f"status    : {policy.get('status')}")
print(f"tier      : {policy.get('tier')}")

# Step 4: Simulate disruption
print("\n=== STEP 4: Simulate disruption event ===")
r = requests.post(f"{BASE}/disruptions/simulate?city=Mumbai&pincode=400001", headers=H)
events = r.json()
if isinstance(events, list) and events:
    event = events[0]
    EVENT_ID = event["id"]
    print(f"event_id  : {EVENT_ID}")
    print(f"type      : {event['disruption_type']}")
    print(f"severity  : {event['severity']}")
    print(f"dss       : {event['dss_multiplier']}")
else:
    print(f"ERROR: {events}")
    sys.exit(1)

# Step 5: Check disruption notification
print("\n=== STEP 5: Check disruption_detected notification ===")
r = requests.get(f"{BASE}/notifications/", headers=H)
notifs = r.json()
disruption_notifs = [n for n in notifs if n["type"] == "disruption_detected" and n["ref_id"] == EVENT_ID]
if disruption_notifs:
    n = disruption_notifs[0]
    print(f"[OK] disruption_detected notification found")
    print(f"     title : {n['title']}")
    print(f"     body  : {n['body']}")
    print(f"     ref_id: {n['ref_id']}")
else:
    print("[FAIL] No disruption_detected notification found!")

# Step 6: Trigger claim
print("\n=== STEP 6: Trigger claim ===")
r = requests.post(f"{BASE}/claims/trigger/{EVENT_ID}", headers=H)
claim = r.json()
if "id" in claim:
    CLAIM_ID = claim["id"]
    print(f"claim_id  : {CLAIM_ID}")
    print(f"status    : {claim['status']}")
    print(f"amount    : Rs.{claim.get('approved_amount')}")
    print(f"fraud_score: {claim.get('fraud_score')}")
else:
    print(f"ERROR: {claim}")
    sys.exit(1)

# Step 7: Check claim notifications
print("\n=== STEP 7: Check claim notifications ===")
r = requests.get(f"{BASE}/notifications/", headers=H)
notifs = r.json()
for ntype in ["claim_approved", "claim_paid", "claim_rejected"]:
    matches = [n for n in notifs if n["type"] == ntype and n["ref_id"] == CLAIM_ID]
    if matches:
        n = matches[0]
        print(f"[OK] {ntype}")
        print(f"     title : {n['title']}")
        print(f"     body  : {n['body']}")

# Step 8: Check payout
print("\n=== STEP 8: Check payout ===")
r = requests.get(f"{BASE}/payouts/", headers=H)
payouts = r.json()
claim_payouts = [p for p in payouts if p.get("claim_id") == CLAIM_ID]
if claim_payouts:
    p = claim_payouts[0]
    print(f"[OK] Payout found")
    print(f"     payout_id : {p['id']}")
    print(f"     amount    : Rs.{p['amount']}")
    print(f"     status    : {p['status']}")
    print(f"     channel   : {p.get('channel')}")
    print(f"     tx_ref    : {p.get('transaction_ref')}")
else:
    print("[FAIL] No payout found for this claim!")

print("\n=== SUMMARY ===")
print(f"Event created     : {'OK' if EVENT_ID else 'FAIL'}")
print(f"Disruption notif  : {'OK' if disruption_notifs else 'FAIL'}")
print(f"Claim status      : {claim.get('status','FAIL')}")
print(f"Payout            : {'OK' if claim_payouts else 'FAIL'}")
print()
