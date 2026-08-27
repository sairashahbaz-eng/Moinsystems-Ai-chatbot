from datetime import datetime, timezone
from uuid import uuid4

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.db.models import ChatSession


router = APIRouter(
    prefix="/api/v1/sessions",
    tags=["Sessions"],
)


@router.post("")
def create_session(
    source_page: str | None = None,
    db: Session = Depends(get_db),
):
    now = datetime.now(timezone.utc)

    chat_session = ChatSession(
        session_token=str(uuid4()),
        last_activity_at=now,
        source_page=source_page,
        status="active",
    )

    db.add(chat_session)
    db.commit()
    db.refresh(chat_session)

    return {
        "session_id": chat_session.id,
        "session_token": chat_session.session_token,
        "status": chat_session.status,
    }