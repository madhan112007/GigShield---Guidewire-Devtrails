"""
SUSANOO CONTEXT BUILDER
Injects real-time worker data from DB into agent prompts.
"""
from datetime import datetime, timezone
from typing import Optional
from app.models.models import Worker, Policy, Claim, Payout, DisruptionEvent


class ContextBuilder:

    def build(
        self,
        worker: Worker,
        active_policy: Optional[Policy] = None,
        recent_claims: list = None,
        recent_payouts: list = None,
        active_disruptions: list = None,
    ) -> str:
        parts = []

        # Worker profile
        parts.append(
            f"WORKER: {worker.name or 'Unknown'} | "
            f"City: {worker.city} | Pincode: {worker.pincode} | "
            f"Platform: {worker.platform} | "
            f"Avg daily earnings: ₹{worker.avg_daily_earnings or 0} | "
            f"Verified: {worker.is_verified}"
        )

        # Active policy
        if active_policy:
            now = datetime.now(timezone.utc)
            end = active_policy.end_date
            if end.tzinfo is None:
                end = end.replace(tzinfo=timezone.utc)
            days_left = (end - now).days
            parts.append(
                f"POLICY: {active_policy.tier.upper()} | "
                f"Premium: ₹{active_policy.weekly_premium}/week | "
                f"Daily cap: ₹{active_policy.max_daily_payout} | "
                f"Weekly cap: ₹{active_policy.max_weekly_payout} | "
                f"Expires: {end.strftime('%d %b %Y')} ({days_left}d left) | "
                f"Total claimed: ₹{active_policy.total_claimed or 0} | "
                f"Status: {active_policy.status}"
            )
        else:
            parts.append("POLICY: None active")

        # Recent claims
        if recent_claims:
            claim_lines = []
            for c in recent_claims[:5]:
                status = c.status.value.upper()
                amount = f"₹{c.approved_amount or 0}"
                fraud = f"fraud={c.fraud_score:.0f}"
                flags = c.fraud_flags or "none"
                date = c.created_at.strftime("%d %b")
                claim_lines.append(f"  [{status}] {amount} | {fraud} | flags={flags} | {date}")
            parts.append("RECENT CLAIMS:\n" + "\n".join(claim_lines))

        # Recent payouts
        if recent_payouts:
            payout_lines = []
            for p in recent_payouts[:3]:
                status = p.status.value.upper()
                channel = p.channel or "UPI"
                ref = p.transaction_ref or "N/A"
                secs = p.settlement_seconds or 0
                date = p.initiated_at.strftime("%d %b")
                payout_lines.append(
                    f"  [{status}] ₹{p.amount} via {channel} | ref={ref} | {secs}s | {date}"
                )
            parts.append("RECENT PAYOUTS:\n" + "\n".join(payout_lines))

        # Active disruptions
        if active_disruptions:
            d_lines = []
            for d in active_disruptions:
                d_lines.append(
                    f"  {d.disruption_type.value.upper()} | severity={d.severity.value} | "
                    f"DSS={d.dss_multiplier} | raw={d.raw_value}"
                )
            parts.append(f"ACTIVE DISRUPTIONS IN {worker.city}:\n" + "\n".join(d_lines))
        else:
            parts.append(f"ACTIVE DISRUPTIONS IN {worker.city}: None currently")

        return "\n".join(parts)

    def detect_language(self, message: str) -> str:
        msg = message.lower()
        hindi = ["hai", "hua", "kya", "nahi", "mera", "aap", "kab", "kyun", "bhi", "mein", "aaya", "nahi"]
        tamil = ["enaku", "yen", "unga", "naan", "illai", "irukku", "seyya", "theriyuma", "pannunga"]
        if sum(1 for w in hindi if w in msg) >= 2:
            return "hi"
        if sum(1 for w in tamil if w in msg) >= 2:
            return "ta"
        return "en"
