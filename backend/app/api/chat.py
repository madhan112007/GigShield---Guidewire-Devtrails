"""
SUSANOO CHAT API
POST /api/v1/chat/send     — Send message to SUSHI multi-agent chatbot
GET  /api/v1/chat/history  — Get last 50 messages
POST /api/v1/chat/feedback — Rate a bot response
"""
import json
import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timezone

from app.database import get_db
from app.models.models import (
    Worker, Policy, Claim, Payout, DisruptionEvent,
    ChatMessage, PolicyStatus, ClaimStatus,
)
from app.services.auth_service import get_current_worker
from app.services.ai.orchestrator import chat as agent_chat

router = APIRouter()


# ── Schemas ───────────────────────────────────────────────────────────────────

class ChatSendRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None


class ChatSendResponse(BaseModel):
    message_id: str
    conversation_id: str
    answer: str
    intent: str
    should_escalate: bool
    escalation_reason: Optional[str]
    suggested_actions: List[str]
    confidence: float
    agent_used: str
    language: str


class ChatMessageOut(BaseModel):
    id: str
    sender_type: str
    content: str
    intent: Optional[str]
    should_escalate: bool
    suggested_actions: List[str]
    agent_used: Optional[str]
    language: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class FeedbackRequest(BaseModel):
    message_id: str
    rating: int  # 1-5
    comment: Optional[str] = None


# ── Helpers ───────────────────────────────────────────────────────────────────

async def _get_worker_context(worker: Worker, db: AsyncSession) -> dict:
    """Fetch all context needed by the AI agents in one pass."""
    now = datetime.now(timezone.utc)

    # Active policy
    result = await db.execute(
        select(Policy).where(
            Policy.worker_id == worker.id,
            Policy.status == PolicyStatus.ACTIVE,
        ).order_by(Policy.created_at.desc())
    )
    active_policy = None
    for p in result.scalars().all():
        end = p.end_date.replace(tzinfo=timezone.utc) if p.end_date.tzinfo is None else p.end_date
        if end >= now:
            active_policy = p
            break

    # Recent claims
    result = await db.execute(
        select(Claim).where(Claim.worker_id == worker.id)
        .order_by(Claim.created_at.desc()).limit(5)
    )
    recent_claims = result.scalars().all()

    # Recent payouts
    result = await db.execute(
        select(Payout).where(Payout.worker_id == worker.id)
        .order_by(Payout.initiated_at.desc()).limit(3)
    )
    recent_payouts = result.scalars().all()

    # Active disruptions in worker's city
    result = await db.execute(
        select(DisruptionEvent).where(
            DisruptionEvent.city == worker.city,
            DisruptionEvent.is_active == True,
        )
    )
    active_disruptions = result.scalars().all()

    return {
        "active_policy": active_policy,
        "recent_claims": list(recent_claims),
        "recent_payouts": list(recent_payouts),
        "active_disruptions": list(active_disruptions),
    }


async def _get_history(worker_id: str, conversation_id: str, db: AsyncSession) -> list:
    """Get last 10 turns for conversation context."""
    result = await db.execute(
        select(ChatMessage).where(
            ChatMessage.worker_id == worker_id,
            ChatMessage.conversation_id == conversation_id,
        ).order_by(ChatMessage.created_at.desc()).limit(10)
    )
    messages = list(reversed(result.scalars().all()))
    return [{"role": "user" if m.sender_type == "user" else "assistant", "content": m.content} for m in messages]


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post("/send", response_model=ChatSendResponse)
async def send_message(
    payload: ChatSendRequest,
    db: AsyncSession = Depends(get_db),
    worker: Worker = Depends(get_current_worker),
):
    message = payload.message.strip()
    if not message:
        raise HTTPException(status_code=400, detail="Message cannot be empty")
    if len(message) > 500:
        raise HTTPException(status_code=400, detail="Message too long (max 500 chars)")

    conversation_id = payload.conversation_id or str(uuid.uuid4())

    # Fetch worker context
    ctx = await _get_worker_context(worker, db)

    # Fetch conversation history
    history = await _get_history(worker.id, conversation_id, db)

    # Save user message
    user_msg = ChatMessage(
        worker_id=worker.id,
        conversation_id=conversation_id,
        sender_type="user",
        content=message,
        is_read=True,
    )
    db.add(user_msg)
    await db.flush()

    # Run multi-agent orchestrator
    result = await agent_chat(
        message=message,
        worker=worker,
        active_policy=ctx["active_policy"],
        recent_claims=ctx["recent_claims"],
        recent_payouts=ctx["recent_payouts"],
        active_disruptions=ctx["active_disruptions"],
        history=history,
    )

    # Save bot response
    bot_msg = ChatMessage(
        worker_id=worker.id,
        conversation_id=conversation_id,
        sender_type="bot",
        content=result["answer"],
        intent=result.get("intent"),
        should_escalate=result.get("should_escalate", False),
        escalation_reason=result.get("escalation_reason"),
        suggested_actions=json.dumps(result.get("suggested_actions", [])),
        confidence=result.get("confidence"),
        agent_used=result.get("agent_used"),
        language=result.get("language", "en"),
    )
    db.add(bot_msg)
    await db.commit()
    await db.refresh(bot_msg)

    return ChatSendResponse(
        message_id=bot_msg.id,
        conversation_id=conversation_id,
        answer=result["answer"],
        intent=result.get("intent", "general"),
        should_escalate=result.get("should_escalate", False),
        escalation_reason=result.get("escalation_reason"),
        suggested_actions=result.get("suggested_actions", []),
        confidence=result.get("confidence", 0.0),
        agent_used=result.get("agent_used", "unknown"),
        language=result.get("language", "en"),
    )


@router.get("/history", response_model=List[ChatMessageOut])
async def get_history(
    db: AsyncSession = Depends(get_db),
    worker: Worker = Depends(get_current_worker),
):
    result = await db.execute(
        select(ChatMessage).where(ChatMessage.worker_id == worker.id)
        .order_by(ChatMessage.created_at.desc()).limit(50)
    )
    messages = list(reversed(result.scalars().all()))
    out = []
    for m in messages:
        actions = []
        if m.suggested_actions:
            try:
                actions = json.loads(m.suggested_actions)
            except Exception:
                pass
        out.append(ChatMessageOut(
            id=m.id,
            sender_type=m.sender_type,
            content=m.content,
            intent=m.intent,
            should_escalate=m.should_escalate or False,
            suggested_actions=actions,
            agent_used=m.agent_used,
            language=m.language,
            created_at=m.created_at,
        ))
    return out


@router.post("/feedback")
async def submit_feedback(
    payload: FeedbackRequest,
    db: AsyncSession = Depends(get_db),
    worker: Worker = Depends(get_current_worker),
):
    if not 1 <= payload.rating <= 5:
        raise HTTPException(status_code=400, detail="Rating must be 1-5")

    result = await db.execute(
        select(ChatMessage).where(
            ChatMessage.id == payload.message_id,
            ChatMessage.worker_id == worker.id,
        )
    )
    msg = result.scalar_one_or_none()
    if not msg:
        raise HTTPException(status_code=404, detail="Message not found")

    # Store feedback in the message metadata field (reuse suggested_actions as temp store)
    # In production, add a separate ChatFeedback table
    existing = {}
    try:
        existing = json.loads(msg.suggested_actions or "{}")
    except Exception:
        pass
    if isinstance(existing, list):
        existing = {}
    existing["feedback_rating"] = payload.rating
    existing["feedback_comment"] = payload.comment
    msg.suggested_actions = json.dumps(existing)
    await db.commit()

    return {"ok": True, "rating": payload.rating}
