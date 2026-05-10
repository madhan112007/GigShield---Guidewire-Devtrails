import asyncio, sys
sys.path.insert(0, '.')

async def check():
    from app.database import AsyncSessionLocal
    from sqlalchemy import select
    from app.models.models import Worker, Claim, Payout, DisruptionEvent, Policy

    async with AsyncSessionLocal() as db:
        # Latest claim
        result = await db.execute(select(Claim).order_by(Claim.created_at.desc()).limit(1))
        claim = result.scalar_one_or_none()
        if not claim:
            print('No claim found'); return

        w = (await db.execute(select(Worker).where(Worker.id == claim.worker_id))).scalar_one_or_none()
        e = (await db.execute(select(DisruptionEvent).where(DisruptionEvent.id == claim.disruption_event_id))).scalar_one_or_none()
        p = (await db.execute(select(Policy).where(Policy.id == claim.policy_id))).scalar_one_or_none()
        payout = (await db.execute(select(Payout).where(Payout.claim_id == claim.id))).scalar_one_or_none()

        print("=== WORKER ===")
        print(f"avg_daily_earnings : Rs.{w.avg_daily_earnings}")
        print(f"city               : {w.city}")
        print(f"pincode            : {w.pincode}")

        print("\n=== DISRUPTION EVENT ===")
        print(f"type               : {e.disruption_type.value}")
        print(f"severity           : {e.severity.value}")
        print(f"raw dss_multiplier : {e.dss_multiplier}  (stored at event creation)")

        print("\n=== POLICY ===")
        print(f"tier               : {p.tier.value}")
        print(f"max_daily_payout   : Rs.{p.max_daily_payout}")
        print(f"max_weekly_payout  : Rs.{p.max_weekly_payout}")
        print(f"total_claimed      : Rs.{p.total_claimed}")

        print("\n=== CLAIM (stored values) ===")
        print(f"worker_daily_avg   : Rs.{claim.worker_daily_avg}")
        print(f"dss_multiplier     : {claim.dss_multiplier}  (infra-adjusted)")
        print(f"active_hours_ratio : {claim.active_hours_ratio}")
        print(f"fraud_score        : {claim.fraud_score}")
        print(f"auto_approved      : {claim.auto_approved}")
        print(f"claimed_amount     : Rs.{claim.claimed_amount}")
        print(f"approved_amount    : Rs.{claim.approved_amount}")
        print(f"status             : {claim.status.value}")

        print("\n=== PAYOUT ===")
        print(f"amount             : Rs.{payout.amount}")
        print(f"status             : {payout.status.value}")
        print(f"channel            : {payout.channel}")
        print(f"transaction_ref    : {payout.transaction_ref}")

        print("\n=== MANUAL VERIFICATION ===")
        daily = float(claim.worker_daily_avg)
        dss   = float(claim.dss_multiplier)
        hrs   = float(claim.active_hours_ratio)
        raw   = round(daily * dss * hrs, 2)
        print(f"Formula : daily_avg x dss x hours_ratio")
        print(f"        : {daily} x {dss} x {hrs}")
        print(f"        = Rs.{raw}")
        print(f"Stored  = Rs.{claim.approved_amount}")
        print(f"Match   : {'YES' if abs(raw - float(claim.approved_amount)) < 0.02 else 'NO - MISMATCH!'}")

        print("\n=== CAP CHECK ===")
        from app.services.platform_service import get_city_economics
        col, _ = get_city_economics(w.city)
        daily_cap = round(p.max_daily_payout * col, 2)
        print(f"city CoL index     : {col}")
        print(f"max_daily_payout   : Rs.{p.max_daily_payout}")
        print(f"CoL-adjusted cap   : Rs.{daily_cap}")
        print(f"approved_amount    : Rs.{claim.approved_amount}")
        print(f"Within cap         : {'YES' if float(claim.approved_amount) <= daily_cap else 'NO - EXCEEDS CAP!'}")

asyncio.run(check())
