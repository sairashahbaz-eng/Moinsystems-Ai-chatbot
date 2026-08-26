from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.chat.service import chat_service


router = APIRouter(
    prefix="/api/v1/chat",
    tags=["Chat"],
)


class ChatRequest(BaseModel):
    question: str = Field(..., min_length=1)
    recent_messages: list[dict[str, str]] = []
    intent: str | None = None
    lead_state: str | None = None


class ChatResponse(BaseModel):
    answer: str
    grounded: bool


@router.post("/messages", response_model=ChatResponse)
def chat(request: ChatRequest):
    result = chat_service.chat(
        message=request.question,
        recent_messages=request.recent_messages,
        intent=request.intent,
        lead_state=request.lead_state,
    )

    return ChatResponse(
        answer=result["answer"],
        grounded=result["grounded"],
    )