"""
SUSANOO MULTI-AGENT ORCHESTRATOR
Flow:
  User message
      ↓
  OrchestratorAgent  → routes to specialist
      ↓
  SpecialistAgent    → generates response with real context
      ↓
  EscalationAgent    → intercepts if escalation needed
      ↓
  Structured JSON response

Agents:
  - OrchestratorAgent  : intent detection + routing
  - ClaimAgent         : claim status, fraud flags
  - PayoutAgent        : UPI/IMPS settlement queries
  - PolicyAgent        : tier comparison, coverage, premium
  - DisruptionAgent    : active disruptions, DSS scores
  - EscalationAgent    : legal threats, payout delays >48h
"""
import json
import logging
import re
from typing import Optional
from app.services.ai import bedrock_client
from app.services.ai.prompts import (
    ORCHESTRATOR_PROMPT,
    CLAIM_AGENT_PROMPT,
    PAYOUT_AGENT_PROMPT,
    POLICY_AGENT_PROMPT,
    DISRUPTION_AGENT_PROMPT,
    ESCALATION_AGENT_PROMPT,
    ContextBuilder,
    FEW_SHOTS,
)

logger = logging.getLogger(__name__)

AGENT_PROMPTS = {
    "claim_agent":      CLAIM_AGENT_PROMPT,
    "payout_agent":     PAYOUT_AGENT_PROMPT,
    "policy_agent":     POLICY_AGENT_PROMPT,
    "disruption_agent": DISRUPTION_AGENT_PROMPT,
    "escalation_agent": ESCALATION_AGENT_PROMPT,
}

# Keyword-based fallback routing (no LLM needed)
KEYWORD_ROUTES = {
    "claim_agent":      ["claim", "reject", "approve", "fraud", "flag", "hua kya", "status"],
    "payout_agent":     ["payout", "money", "upi", "imps", "transfer", "credit", "nahi aaya", "payment"],
    "policy_agent":     ["policy", "tier", "premium", "basic", "smart", "pro", "cover", "plan"],
    "disruption_agent": ["rain", "heat", "aqi", "disruption", "bandh", "curfew", "active", "alert"],
    "escalation_agent": ["court", "lawyer", "irda", "refund", "2 din", "2 days", "police", "media", "twitter"],
}

_context_builder = ContextBuilder()


def _extract_json(text: str) -> dict:
    """Extract JSON from LLM response — handles markdown code blocks and raw JSON."""
    # Try direct parse first
    try:
        return json.loads(text.strip())
    except Exception:
        pass
    # Try extracting from markdown code block
    match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except Exception:
            pass
    # Try finding first { ... } block
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0))
        except Exception:
            pass
    return {}


def _keyword_route(message: str) -> str:
    """Fast keyword-based routing — used as fallback if orchestrator LLM fails."""
    msg = message.lower()
    scores = {agent: 0 for agent in KEYWORD_ROUTES}
    for agent, keywords in KEYWORD_ROUTES.items():
        for kw in keywords:
            if kw in msg:
                scores[agent] += 1
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else "claim_agent"


def _safe_response(message: str, language: str = "en") -> dict:
    """Fallback response when all LLM calls fail."""
    if language == "hi":
        answer = "Abhi system busy hai. Thodi der mein try karein ya support se contact karein."
    elif language == "ta":
        answer = "System busy aagirukku. Konjam neram kazhichu try pannunga."
    else:
        answer = "System is busy right now. Please try again in a moment or contact support."
    return {
        "answer": answer,
        "intent": "general",
        "should_escalate": False,
        "escalation_reason": None,
        "suggested_actions": ["Contact Support"],
        "confidence": 0.0,
        "agent_used": "fallback",
    }


async def _run_orchestrator(message: str, language: str) -> str:
    """Step 1: Route message to correct agent."""
    messages = [{"role": "user", "content": message}]
    try:
        raw = await bedrock_client.invoke(messages, ORCHESTRATOR_PROMPT, max_tokens=100)
        parsed = _extract_json(raw)
        route = parsed.get("route", "")
        if route in AGENT_PROMPTS:
            return route
    except Exception as e:
        logger.warning(f"[Orchestrator] LLM failed: {e}, using keyword routing")
    return _keyword_route(message)


async def _run_agent(
    agent_name: str,
    message: str,
    context: str,
    history: list,
    language: str,
) -> dict:
    """Step 2: Run the specialist agent with full context."""
    system = AGENT_PROMPTS[agent_name]

    # Build messages: few-shots + context injection + history + current message
    messages = []

    # Add relevant few-shots (max 3 to save tokens)
    for shot in FEW_SHOTS[:6]:
        messages.append(shot)

    # Inject context as a system-level user message
    if context:
        messages.append({
            "role": "user",
            "content": f"[WORKER CONTEXT]\n{context}\n[END CONTEXT]",
        })
        messages.append({
            "role": "assistant",
            "content": '{"answer": "Context received.", "intent": "general", "should_escalate": false, "escalation_reason": null, "suggested_actions": [], "confidence": 1.0}',
        })

    # Add conversation history (last 6 turns)
    for turn in history[-6:]:
        messages.append({"role": turn["role"], "content": turn["content"]})

    # Language hint
    lang_hint = ""
    if language == "hi":
        lang_hint = " [Respond in Hinglish]"
    elif language == "ta":
        lang_hint = " [Respond in Tanglish]"

    messages.append({"role": "user", "content": message + lang_hint})

    try:
        raw = await bedrock_client.invoke(messages, system, max_tokens=400)
        parsed = _extract_json(raw)
        if parsed and "answer" in parsed:
            parsed["agent_used"] = agent_name
            return parsed
        # LLM returned text but not valid JSON — wrap it
        if raw.strip():
            return {
                "answer": raw.strip()[:300],
                "intent": "general",
                "should_escalate": False,
                "escalation_reason": None,
                "suggested_actions": [],
                "confidence": 0.5,
                "agent_used": agent_name,
            }
    except Exception as e:
        logger.error(f"[{agent_name}] failed: {e}")

    return {}


async def chat(
    message: str,
    worker=None,
    active_policy=None,
    recent_claims: list = None,
    recent_payouts: list = None,
    active_disruptions: list = None,
    history: list = None,
) -> dict:
    """
    Main entry point for the multi-agent chatbot.

    Args:
        message: User's message
        worker: Worker ORM object (optional but recommended)
        active_policy: Worker's active policy (optional)
        recent_claims: Last 5 claims (optional)
        recent_payouts: Last 3 payouts (optional)
        active_disruptions: Active disruptions in worker's city (optional)
        history: List of {"role": "user"|"assistant", "content": "..."} dicts

    Returns:
        {
            "answer": str,
            "intent": str,
            "should_escalate": bool,
            "escalation_reason": str | None,
            "suggested_actions": list[str],
            "confidence": float,
            "agent_used": str,
            "language": str,
        }
    """
    history = history or []

    # Detect language
    language = _context_builder.detect_language(message)

    # Build context from real DB data
    context = ""
    if worker:
        context = _context_builder.build(
            worker=worker,
            active_policy=active_policy,
            recent_claims=recent_claims or [],
            recent_payouts=recent_payouts or [],
            active_disruptions=active_disruptions or [],
        )

    # Step 1: Route
    agent_name = await _run_orchestrator(message, language)
    logger.info(f"[Orchestrator] routed to {agent_name} | lang={language}")

    # Step 2: Run specialist agent
    result = await _run_agent(agent_name, message, context, history, language)

    if not result:
        return _safe_response(message, language)

    result["language"] = language

    # Step 3: Escalation override — if escalation keywords detected, always escalate
    escalation_keywords = ["consumer court", "lawyer", "irda", "police", "media", "2 din", "2 days", "48 hour"]
    if any(kw in message.lower() for kw in escalation_keywords):
        result["should_escalate"] = True
        result["escalation_reason"] = result.get("escalation_reason") or "Escalation keyword detected"
        result["agent_used"] = "escalation_agent"

    return result
