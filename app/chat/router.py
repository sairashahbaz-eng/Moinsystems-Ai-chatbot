from fastapi import APIRouter
from pydantic import BaseModel

from app.chat.service import ask_chatbot


router = APIRouter(
    prefix="/api/v1/chat",
    tags=["Chat"]
)


class ChatRequest(BaseModel):
    question: str


class ChatResponse(BaseModel):
    answer: str


@router.post("/", response_model=ChatResponse)
def chat(request: ChatRequest):
    answer = ask_chatbot(request.question)

    return ChatResponse(
        answer=answer
    )