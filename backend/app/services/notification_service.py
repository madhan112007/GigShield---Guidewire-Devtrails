"""
Notification Service — in-app + FCM push notifications for claim lifecycle events.
Uses FCM HTTP V1 API (Legacy API deprecated June 2024) with Service Account auth.
Stores notifications in DB for in-app feed; optionally fires FCM push if configured.
"""
from __future__ import annotations
import json
import httpx
from typing import Optional
from app.config import settings

_SCOPES = ["https://www.googleapis.com/auth/firebase.messaging"]

_TEMPLATES = {
    "claim_approved": {
        "title": "Claim Approved ✅",
        "body": "Rs.{amount} approved for {disruption} disruption. Payout initiated.",
    },
    "claim_rejected": {
        "title": "Claim Rejected ❌",
        "body": "Your claim was rejected: {reason}",
    },
    "claim_paid": {
        "title": "Payment Credited 💰",
        "body": "Rs.{amount} credited to {upi_id}. Ref: {ref}",
    },
    "disruption_detected": {
        "title": "Disruption Alert ⚠️",
        "body": "{severity} {disruption} detected in {city}. Your policy is active.",
    },
    "policy_expiring": {
        "title": "Policy Expiring Soon 🔔",
        "body": "Your GigShield policy expires in {days} day(s). Renew to stay protected.",
    },
}


def _get_access_token() -> Optional[str]:
    """Get OAuth2 access token from Service Account JSON for FCM V1 API."""
    sa_path = settings.FCM_SERVICE_ACCOUNT_PATH.strip()
    if not sa_path or sa_path == "mock_key":
        return None
    try:
        from google.oauth2 import service_account
        import google.auth.transport.requests
        creds = service_account.Credentials.from_service_account_file(
            sa_path, scopes=_SCOPES
        )
        creds.refresh(google.auth.transport.requests.Request())
        return creds.token
    except Exception as e:
        print(f"[FCM] Service account auth failed: {e}")
        return None


async def _send_fcm(fcm_token: str, title: str, body: str, data: dict) -> bool:
    """Send push via FCM HTTP V1 API."""
    project_id = settings.FCM_PROJECT_ID.strip()
    access_token = _get_access_token()
    if not access_token or not project_id or project_id == "mock_key":
        print(f"[FCM] Push (not configured): {title} — {body}")
        return True
    url = f"https://fcm.googleapis.com/v1/projects/{project_id}/messages:send"
    try:
        async with httpx.AsyncClient() as client:
            r = await client.post(
                url,
                headers={"Authorization": f"Bearer {access_token}"},
                json={
                    "message": {
                        "token": fcm_token,
                        "notification": {"title": title, "body": body},
                        "data": {k: str(v) for k, v in data.items()},
                        "android": {"priority": "high"},
                    }
                },
                timeout=8.0,
            )
            return r.status_code == 200
    except Exception as e:
        print(f"[FCM ERROR] {e}")
        return False


async def _persist_notification(db, worker_id: str, title: str, body: str, notif_type: str, ref_id: str = ""):
    """Store notification in DB for in-app feed."""
    from app.models.models import WorkerNotification
    notif = WorkerNotification(
        worker_id=worker_id,
        title=title,
        body=body,
        notif_type=notif_type,
        ref_id=ref_id,
    )
    db.add(notif)
    await db.flush()


async def notify_claim_approved(db, worker, claim, disruption_type: str):
    t = _TEMPLATES["claim_approved"]
    title = t["title"]
    body = t["body"].format(amount=int(claim.approved_amount or 0), disruption=disruption_type.replace("_", " "))
    await _persist_notification(db, worker.id, title, body, "claim_approved", claim.id)
    if worker.fcm_token:
        await _send_fcm(worker.fcm_token, title, body, {"claim_id": claim.id, "type": "claim_approved"})


async def notify_claim_rejected(db, worker, claim):
    t = _TEMPLATES["claim_rejected"]
    title = t["title"]
    reason = (claim.rejection_reason or "Fraud risk detected")[:80]
    body = t["body"].format(reason=reason)
    await _persist_notification(db, worker.id, title, body, "claim_rejected", claim.id)
    if worker.fcm_token:
        await _send_fcm(worker.fcm_token, title, body, {"claim_id": claim.id, "type": "claim_rejected"})


async def notify_claim_paid(db, worker, claim, upi_id: str, transaction_ref: str):
    t = _TEMPLATES["claim_paid"]
    title = t["title"]
    body = t["body"].format(amount=int(claim.approved_amount or 0), upi_id=upi_id, ref=transaction_ref or "N/A")
    await _persist_notification(db, worker.id, title, body, "claim_paid", claim.id)
    if worker.fcm_token:
        await _send_fcm(worker.fcm_token, title, body, {"claim_id": claim.id, "type": "claim_paid"})


async def notify_disruption_detected(db, worker_ids: list, city: str, severity: str, disruption_type: str, event_id: str):
    """Bulk notify all active workers in a city about a new disruption."""
    from sqlalchemy import select
    from app.models.models import Worker
    t = _TEMPLATES["disruption_detected"]
    title = t["title"]
    body = t["body"].format(
        severity=severity.capitalize(),
        disruption=disruption_type.replace("_", " "),
        city=city,
    )
    workers_result = await db.execute(select(Worker).where(Worker.id.in_(worker_ids)))
    workers = workers_result.scalars().all()
    for w in workers:
        await _persist_notification(db, w.id, title, body, "disruption_detected", event_id)
        if w.fcm_token:
            await _send_fcm(w.fcm_token, title, body, {"event_id": event_id, "type": "disruption_detected"})
