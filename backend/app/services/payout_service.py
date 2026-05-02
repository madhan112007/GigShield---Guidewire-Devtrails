"""
Payout Service
Settlement flow: UPI (primary) -> IMPS bank transfer (fallback) -> Razorpay sandbox (demo)
Rollback logic: if transfer fails mid-way, claim reverts to APPROVED status
Settlement time tracked in seconds from trigger to payout
SMS confirmation sent after successful payout
"""
import uuid
import asyncio
import httpx
import razorpay
from datetime import datetime, timezone
from app.config import settings


def _get_client() -> razorpay.Client:
    return razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))


def _is_mock() -> bool:
    return not settings.RAZORPAY_KEY_ID or settings.RAZORPAY_KEY_ID.startswith("rzp_test_mock")


async def send_payout_sms(phone: str, amount: float, upi_id: str, transaction_ref: str, disruption: str) -> bool:
    """SMS confirmation after payout — zero-touch UX completion."""
    api_key = settings.FAST2SMS_API_KEY.strip() if settings.FAST2SMS_API_KEY else ""
    if not api_key:
        print("[SMS] Payout confirmation (not configured): " + phone + " Rs." + str(int(amount)))
        return True
    number = phone.strip().lstrip("+")
    if number.startswith("91") and len(number) == 12:
        number = number[2:]
    number = number[-10:]
    message = (
        "Susanoo: Rs." + str(int(amount)) +
        " credited to " + upi_id +
        " for " + disruption.replace("_", " ") +
        " disruption. Ref:" + transaction_ref +
        ". Income protected. -Susanoo"
    )
    try:
        url = "https://2factor.in/API/V1/" + api_key + "/SMS/" + number + "/AUTOGEN2/GigShield_Payout"
        async with httpx.AsyncClient() as client:
            r = await client.get(url, timeout=10.0)
            print("[SMS] Sent to " + number + " status=" + str(r.json().get("Status")))
        return True
    except (httpx.HTTPError, ValueError) as e:
        print("[SMS ERROR] " + str(e))
        return False


async def _razorpay_upi_payout(worker_id: str, upi_id: str, amount: float, claim_id: str) -> dict:
    """Primary channel: UPI via Razorpay X."""
    try:
        client = _get_client()
        amount_paise = int(amount * 100)
        loop = asyncio.get_event_loop()
        payout = await loop.run_in_executor(
            None,
            lambda: client.payout.create({
                "account_number": settings.RAZORPAY_ACCOUNT_NUMBER,
                "fund_account": {
                    "account_type": "vpa",
                    "vpa": {"address": upi_id},
                    "contact": {
                        "name": "GigShield Worker",
                        "type": "customer",
                        "reference_id": worker_id,
                    },
                },
                "amount": amount_paise,
                "currency": "INR",
                "mode": "UPI",
                "purpose": "payout",
                "queue_if_low_balance": True,
                "reference_id": "GS_" + claim_id[:8].upper(),
                "narration": "GigShield Claim Payout",
            })
        )
        success = payout.get("status") in ("processing", "processed", "queued")
        return {
            "success": success,
            "channel": "UPI",
            "payout_id": payout.get("id"),
            "transaction_ref": payout.get("reference_id"),
            "status": payout.get("status"),
        }
    except (razorpay.errors.BadRequestError, razorpay.errors.ServerError, ValueError) as e:
        return {"success": False, "channel": "UPI", "error": str(e)}


async def _razorpay_imps_payout(worker_id: str, bank_account: str, bank_ifsc: str, amount: float, claim_id: str) -> dict:
    """Fallback channel: IMPS bank transfer if UPI not linked."""
    try:
        client = _get_client()
        amount_paise = int(amount * 100)
        loop = asyncio.get_event_loop()
        payout = await loop.run_in_executor(
            None,
            lambda: client.payout.create({
                "account_number": settings.RAZORPAY_ACCOUNT_NUMBER,
                "fund_account": {
                    "account_type": "bank_account",
                    "bank_account": {
                        "name": "GigShield Worker",
                        "ifsc": bank_ifsc,
                        "account_number": bank_account,
                    },
                    "contact": {
                        "name": "GigShield Worker",
                        "type": "customer",
                        "reference_id": worker_id,
                    },
                },
                "amount": amount_paise,
                "currency": "INR",
                "mode": "IMPS",
                "purpose": "payout",
                "queue_if_low_balance": True,
                "reference_id": "GS_IMPS_" + claim_id[:8].upper(),
                "narration": "GigShield Claim Payout (IMPS)",
            })
        )
        success = payout.get("status") in ("processing", "processed", "queued")
        return {
            "success": success,
            "channel": "IMPS",
            "payout_id": payout.get("id"),
            "transaction_ref": payout.get("reference_id"),
            "status": payout.get("status"),
        }
    except (razorpay.errors.BadRequestError, razorpay.errors.ServerError, ValueError) as e:
        return {"success": False, "channel": "IMPS", "error": str(e)}


async def initiate_upi_payout(
    worker_id: str,
    upi_id: str,
    amount: float,
    claim_id: str,
    phone: str = "",
    disruption_type: str = "weather",
    bank_account: str = "",
    bank_ifsc: str = "",
    trigger_time: datetime = None,
) -> dict:
    """
    Settlement flow:
    1. Try UPI (primary — instant, preferred)
    2. If UPI fails and bank details exist, try IMPS (fallback)
    3. If both fail, rollback — claim stays APPROVED for retry
    4. On success, send SMS confirmation
    5. Track settlement_seconds from trigger to payout
    """
    start = datetime.now(timezone.utc)

    if _is_mock():
        result = await _mock_payout(upi_id, amount, claim_id)
        result["channel"] = "SANDBOX"
    else:
        # Step 1: Try UPI
        result = await _razorpay_upi_payout(worker_id, upi_id, amount, claim_id)

        # Step 2: IMPS fallback if UPI fails and bank details available
        if not result["success"] and bank_account and bank_ifsc:
            print("[Payout] UPI failed, trying IMPS fallback for claim " + claim_id)
            result = await _razorpay_imps_payout(worker_id, bank_account, bank_ifsc, amount, claim_id)

        # Step 3: Rollback signal if both channels fail
        if not result["success"]:
            result["rollback"] = True
            result["message"] = "Both UPI and IMPS failed. Claim reverted to APPROVED for retry."
            print("[Payout ROLLBACK] claim=" + claim_id + " amount=" + str(amount))

    # Settlement time in seconds
    settlement_seconds = int((datetime.now(timezone.utc) - start).total_seconds())
    if trigger_time:
        settlement_seconds = int((datetime.now(timezone.utc) - trigger_time).total_seconds())
    result["settlement_seconds"] = settlement_seconds

    # Step 4: SMS confirmation on success
    if result.get("success") and phone:
        await send_payout_sms(
            phone=phone,
            amount=amount,
            upi_id=upi_id,
            transaction_ref=result.get("transaction_ref", "N/A"),
            disruption=disruption_type,
        )

    return result


async def _mock_payout(upi_id: str, amount: float, claim_id: str) -> dict:
    """Mock payout — Razorpay sandbox simulation for demo/hackathon."""
    await asyncio.sleep(0.3)
    return {
        "success": True,
        "payout_id": "pout_mock_" + uuid.uuid4().hex[:12],
        "transaction_ref": "GS" + claim_id[:8].upper(),
        "upi_id": upi_id,
        "amount": amount,
        "status": "completed",
        "completed_at": datetime.utcnow().isoformat(),
        "message": "Rs." + str(int(amount)) + " credited to " + upi_id,
        "rollback": False,
    }
