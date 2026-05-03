"""
SUSANOO — Claim Explanation Service
Generates human-readable, empathetic Hinglish/Tamil explanations
for claim decisions using Amazon Bedrock (Llama3 / Mistral).

Zero technical jargon — written for gig workers on mobile.
"""
from __future__ import annotations

import json
import asyncio
import logging
import boto3
from botocore.config import Config
from botocore.exceptions import ClientError

from app.config import settings
from app.models.models import Claim, Worker, DisruptionEvent, ClaimStatus

logger = logging.getLogger(__name__)

# ── Language detection by city ────────────────────────────────────────────────
_TAMIL_CITIES = {
    "chennai", "coimbatore", "madurai", "tiruchirappalli", "salem",
    "tirunelveli", "vellore", "erode", "tiruppur", "thoothukudi",
}
_HINDI_CITIES = {
    "delhi", "lucknow", "patna", "jaipur", "bhopal", "kanpur",
    "agra", "varanasi", "allahabad", "meerut", "ghaziabad",
}

# ── Disruption type → simple worker-friendly label ───────────────────────────
_DISRUPTION_LABELS = {
    "heavy_rain":         "bahut zyada baarish",
    "extreme_heat":       "bahut zyada garmi",
    "aqi_spike":          "bahut zyada pradushan (AQI)",
    "traffic_disruption": "raaste band / traffic jam",
    "civic_emergency":    "bandh ya curfew",
}

_DISRUPTION_LABELS_TAMIL = {
    "heavy_rain":         "romba adhigama mazhai",
    "extreme_heat":       "romba adhigama veyil",
    "aqi_spike":          "kaathu malinpadu",
    "traffic_disruption": "traffic jam / road block",
    "civic_emergency":    "bandh / curfew",
}

# ── Severity → simple impact label ───────────────────────────────────────────
_SEVERITY_LABELS = {
    "moderate": "thodi",
    "severe":   "bahut",
    "extreme":  "bahut zyada",
}

# ── Fraud flag → worker-friendly explanation ─────────────────────────────────
_FRAUD_EXPLANATIONS = {
    "CITY_MISMATCH":              "aap us shehar mein nahi the jahan disruption hua",
    "GPS_LOCATION_MISMATCH":      "humare system ko lagta hai aap us area mein nahi the",
    "GPS_SPOOF_DETECTED":         "aapki location mein kuch unusual activity detect hui",
    "PLATFORM_INACTIVE":          "us waqt aap delivery platform pe active nahi the",
    "DUPLICATE_CLAIM":            "is disruption ke liye pehle se claim file ho chuka hai",
    "HIGH_CLAIM_FREQUENCY":       "is hafte bahut zyada claims file hue hain",
    "INDIVIDUAL_BASELINE_SPIKE":  "aapke normal pattern se bahut zyada claims hain",
    "ZONE_LOW_CORROBORATION":     "aapke area ke doosre workers ne yeh disruption claim nahi kiya",
    "ZONE_COORDINATED_FRAUD_RISK":"is area mein unusual claim activity detect hui",
}

_FALLBACK = "Aapka claim process hua hai. Details ke liye support se contact karein."


def _detect_language(city: str) -> str:
    c = (city or "").lower().strip()
    if c in _TAMIL_CITIES:
        return "ta"
    if c in _HINDI_CITIES:
        return "hi"
    return "hi"  # default Hinglish


def _disruption_label(disruption_type: str, lang: str) -> str:
    key = disruption_type.lower()
    if lang == "ta":
        return _DISRUPTION_LABELS_TAMIL.get(key, disruption_type.replace("_", " "))
    return _DISRUPTION_LABELS.get(key, disruption_type.replace("_", " "))


def _fraud_reason(fraud_flags_json: str) -> str:
    """Pick the most important fraud flag and return a human-readable reason."""
    try:
        flags = json.loads(fraud_flags_json or "[]")
    except Exception:
        flags = []
    for flag in flags:
        for key, explanation in _FRAUD_EXPLANATIONS.items():
            if key in flag:
                return explanation
    return "kuch technical issue tha"


def _build_prompt(
    claim: Claim,
    worker: Worker,
    disruption: DisruptionEvent,
    lang: str,
) -> str:
    approved = claim.status == ClaimStatus.APPROVED or claim.status == ClaimStatus.PAID
    amount = int(claim.approved_amount or 0)
    disruption_label = _disruption_label(disruption.disruption_type.value, lang)
    severity_label = _SEVERITY_LABELS.get(disruption.severity.value, "")
    fraud_reason = _fraud_reason(claim.fraud_flags or "[]")
    worker_name = (worker.name or "Bhai").split()[0]

    if lang == "ta":
        if approved:
            situation = (
                f"Worker {worker_name} Chennai/Tamil Nadu area-la irukkaaru. "
                f"Avanga claim approve aagirukku. "
                f"Reason: {severity_label} {disruption_label} irundhuchu. "
                f"Amount: Rs.{amount}."
            )
            tone = "Congratulatory, warm Tamil/Tanglish tone."
        else:
            situation = (
                f"Worker {worker_name} claim reject aagirukku. "
                f"Reason: {fraud_reason}."
            )
            tone = "Empathetic, kind Tamil/Tanglish tone. Don't blame the worker."
    else:
        if approved:
            situation = (
                f"Worker {worker_name} ka claim approve hua. "
                f"Reason: {severity_label} {disruption_label} tha. "
                f"Amount: Rs.{amount}."
            )
            tone = "Congratulatory, warm Hinglish tone."
        else:
            situation = (
                f"Worker {worker_name} ka claim reject hua. "
                f"Reason: {fraud_reason}."
            )
            tone = "Empathetic, kind Hinglish tone. Don't blame the worker."

    prompt = f"""You are writing a short push notification for an Indian gig delivery worker about their insurance claim.

SITUATION: {situation}
TONE: {tone}

STRICT RULES:
- Maximum 2-3 sentences only. Short enough for a push notification.
- NEVER use technical words: DSS, multiplier, Isolation Forest, algorithm, lat/long, fraud score, coordinates.
- Use simple everyday Hindi/Hinglish or Tamil/Tanglish words only.
- If approved: mention the amount and reason simply.
- If rejected: be kind, explain simply, suggest contacting support.
- Output ONLY a valid JSON object with a single key "explanation".

Example output format:
{{"explanation": "Aapka claim approve ho gaya! Rs.250 aapke UPI mein aa jayega. Heavy rain ki wajah se aapki income protect hui."}}

Now write the explanation:"""

    return prompt


def _build_body(model_id: str, prompt: str) -> dict:
    if "llama" in model_id:
        return {
            "prompt": (
                "<|begin_of_text|><|start_header_id|>user<|end_header_id|>\n"
                + prompt
                + "<|eot_id|><|start_header_id|>assistant<|end_header_id|>\n"
            ),
            "max_gen_len": 150,
            "temperature": 0.3,
        }
    elif "mistral" in model_id:
        return {
            "prompt": f"<s>[INST] {prompt} [/INST]",
            "max_tokens": 150,
            "temperature": 0.3,
        }
    else:
        # Claude / Anthropic
        return {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 150,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.3,
        }


def _extract_text(model_id: str, body: dict) -> str:
    if "llama" in model_id:
        return body.get("generation", "")
    elif "mistral" in model_id:
        outputs = body.get("outputs", [{}])
        return outputs[0].get("text", "") if outputs else ""
    else:
        content = body.get("content", [{}])
        return content[0].get("text", "") if content else ""


class ClaimExplanationService:

    def __init__(self):
        self._model_id = getattr(settings, "BEDROCK_MODEL_ID", "meta.llama3-8b-instruct-v1:0")
        self._client = boto3.client(
            "bedrock-runtime",
            region_name=getattr(settings, "AWS_REGION", "ap-south-1"),
            config=Config(retries={"max_attempts": 2, "mode": "adaptive"}),
        )

    async def generate_explanation(
        self,
        claim: Claim,
        worker: Worker,
        disruption: DisruptionEvent,
    ) -> str:
        """
        Generate a human-readable, empathetic explanation for a claim decision.
        Returns Hinglish or Tamil text based on worker's city.
        Falls back to a safe default string if Bedrock fails.
        """
        lang = _detect_language(worker.city or "")
        prompt = _build_prompt(claim, worker, disruption, lang)
        body = _build_body(self._model_id, prompt)

        loop = asyncio.get_event_loop()

        for attempt in range(2):  # 1 retry
            try:
                response = await loop.run_in_executor(
                    None,
                    lambda: self._client.invoke_model(
                        modelId=self._model_id,
                        body=json.dumps(body),
                        contentType="application/json",
                        accept="application/json",
                    ),
                )
                raw = json.loads(response["body"].read())
                text = _extract_text(self._model_id, raw).strip()

                # Parse JSON from LLM response
                try:
                    # Handle markdown code blocks
                    if "```" in text:
                        import re
                        match = re.search(r"\{.*?\}", text, re.DOTALL)
                        text = match.group(0) if match else text
                    parsed = json.loads(text)
                    explanation = parsed.get("explanation", "").strip()
                    if explanation:
                        logger.info(f"[ClaimExplanation] claim={claim.id[:8]} lang={lang} ok")
                        return explanation
                except (json.JSONDecodeError, AttributeError):
                    # LLM returned plain text instead of JSON — use it directly if reasonable
                    if len(text) > 10 and len(text) < 300:
                        return text

            except ClientError as e:
                code = e.response["Error"]["Code"]
                if code == "ThrottlingException" and attempt == 0:
                    logger.warning("[ClaimExplanation] Throttled, retrying in 2s...")
                    await asyncio.sleep(2)
                    continue
                logger.error(f"[ClaimExplanation] Bedrock error: {code}")
                break
            except Exception as e:
                logger.error(f"[ClaimExplanation] Unexpected error: {e}")
                break

        # Fallback
        logger.warning(f"[ClaimExplanation] Using fallback for claim={claim.id[:8]}")
        return _FALLBACK


# =============================================================================
# HOW TO INTEGRATE INTO claims.py
# =============================================================================
#
# Step 1 — Import at top of backend/app/api/claims.py:
#
#   from app.services.claim_explanation_service import ClaimExplanationService
#
# Step 2 — After auto-approve logic (around line where claim.status = ClaimStatus.APPROVED):
#
#   # --- CLAIM APPROVED ---
#   if fraud_result["auto_approve"]:
#       claim.status = ClaimStatus.APPROVED
#       claim.approved_amount = round(approved, 2)
#       claim.processed_at = now
#       policy.total_claimed = round(weekly_claimed + approved, 2)
#       policy.claims_count = (policy.claims_count or 0) + 1
#
#       # ADD THESE 3 LINES:
#       explanation = await ClaimExplanationService().generate_explanation(claim, current_worker, event)
#       await notify_claim_approved(db, current_worker, claim, event.disruption_type.value)
#       # Override the generic notification body with AI explanation:
#       # (notification already sent above — use explanation for FCM data payload)
#
# Step 3 — After auto-reject logic (around line where claim.status = ClaimStatus.REJECTED):
#
#   # --- CLAIM REJECTED ---
#   elif fraud_result["auto_reject"]:
#       claim.status = ClaimStatus.REJECTED
#       claim.rejection_reason = "; ".join(fraud_result["flags"])
#       claim.processed_at = now
#
#       # ADD THESE 3 LINES:
#       explanation = await ClaimExplanationService().generate_explanation(claim, current_worker, event)
#       await notify_claim_rejected(db, current_worker, claim)
#       # Send explanation as a separate in-app notification:
#       from app.services.notification_service import _persist_notification
#       await _persist_notification(db, current_worker.id, "Claim Update", explanation, "claim_explanation", claim.id)
#
# =============================================================================
