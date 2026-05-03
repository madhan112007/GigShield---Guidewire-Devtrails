"""
SUSANOO FEW-SHOT EXAMPLES
Teach each agent the correct response format and tone.
"""

FEW_SHOTS = [
    {"role": "user", "content": "mera claim approve hua kya?"},
    {"role": "assistant", "content": '{"answer": "Haan ji ✅ Aapka Heavy Rain claim approve ho gaya! ₹250 aapke UPI mein aa chuka hai.", "intent": "claim_status", "should_escalate": false, "escalation_reason": null, "suggested_actions": ["View Claim Details", "Check Payout Status"], "confidence": 0.95}'},

    {"role": "user", "content": "why my claim rejected??"},
    {"role": "assistant", "content": '{"answer": "Aapka claim reject hua kyunki GPS location mismatch tha ❌ Aapka last GPS ping disruption area se bahar tha. Agar yeh galat hai, support se baat karein.", "intent": "claim_status", "should_escalate": false, "escalation_reason": null, "suggested_actions": ["Talk to Support", "Report GPS Issue"], "confidence": 0.9}'},

    {"role": "user", "content": "payout nahi aaya 2 din ho gaye"},
    {"role": "assistant", "content": '{"answer": "Connecting you to our support team right away. A human agent will contact you within 2 hours.", "intent": "payout_status", "should_escalate": true, "escalation_reason": "Payout delay >48 hours", "suggested_actions": [], "confidence": 0.99}'},

    {"role": "user", "content": "basic aur pro mein kya difference hai"},
    {"role": "assistant", "content": '{"answer": "Tier comparison:\\n🔹 BASIC ₹29/wk → Max ₹300/day, Rain only\\n🔹 SMART ₹49/wk → Max ₹550/day, Rain+Heat+AQI\\n🔹 PRO ₹79/wk → Max ₹750/day, All 5 disruptions", "intent": "policy_info", "should_escalate": false, "escalation_reason": null, "suggested_actions": ["Upgrade to Pro", "Compare Tiers"], "confidence": 0.98}'},

    {"role": "user", "content": "mumbai mein rain disruption active hai kya"},
    {"role": "assistant", "content": '{"answer": "Haan ⚠️ Mumbai mein Heavy Rain ACTIVE hai! DSS: 0.6x (60% income impact). Auto-claim trigger ho raha hai eligible workers ke liye.", "intent": "disruption_info", "should_escalate": false, "escalation_reason": null, "suggested_actions": ["View Active Disruptions"], "confidence": 0.92}'},

    {"role": "user", "content": "consumer court jaaunga agar claim nahi diya"},
    {"role": "assistant", "content": '{"answer": "Connecting you to our support team right away. A human agent will contact you within 2 hours.", "intent": "general", "should_escalate": true, "escalation_reason": "Legal threat - consumer court", "suggested_actions": [], "confidence": 0.99}'},

    {"role": "user", "content": "enaku claim status theriyuma"},
    {"role": "assistant", "content": '{"answer": "Theriyuthu! Unga last claim APPROVED aagirukku ✅ ₹350 UPI-la vanthirukkum. Check pannunga.", "intent": "claim_status", "should_escalate": false, "escalation_reason": null, "suggested_actions": ["View Claim Details"], "confidence": 0.9}'},
]
