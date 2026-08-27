from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.chat.service import chat_service
from app.db.models import ChatSession
from app.db.session import get_db


router = APIRouter(
    prefix="/api/v1/chat",
    tags=["Chat"],
)


class ChatRequest(BaseModel):
    session_token: str = Field(..., min_length=1)
    question: str = Field(..., min_length=1)
    recent_messages: list[dict[str, str]] = []


class ChatResponse(BaseModel):
    answer: str
    grounded: bool
    session_token: str
    intent: str
    lead_state: str | None = None


@router.post("/messages", response_model=ChatResponse)
def chat(
    request: ChatRequest,
    db: Session = Depends(get_db),
):
    # Find the server-created active session
    chat_session = (
        db.query(ChatSession)
        .filter(
            ChatSession.session_token == request.session_token,
            ChatSession.status == "active",
        )
        .first()
    )

    if chat_session is None:
        raise HTTPException(
            status_code=404,
            detail="Invalid or inactive session.",
        )

    # Update session activity
    chat_session.last_activity_at = datetime.now(timezone.utc)

    # Generate response and persist messages
    result = chat_service.chat(
        db=db,
        session_id=chat_session.id,
        message=request.question,
        recent_messages=request.recent_messages,
    )

    lead_state = result.get("lead_state")

    # Answer first, then request the next required field
    if lead_state == "ask_name":
        answer = (
            result["answer"]
            + "\n\nTo help us with your project, please provide your name."
        )

    elif lead_state == "ask_email":
        answer = (
            result["answer"]
            + "\n\nPlease provide your email address."
        )

    elif lead_state == "ask_phone":
        answer = (
            result["answer"]
            + "\n\nPlease provide your contact number."
        )

    else:
        answer = result["answer"]

    db.commit()

    return ChatResponse(
        answer=answer,
        grounded=result["grounded"],
        session_token=chat_session.session_token,
        intent=result["intent"],
        lead_state=lead_state,
    )