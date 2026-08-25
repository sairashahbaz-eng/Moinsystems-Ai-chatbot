from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class ChatSession(Base):
    __tablename__ = "chat_session"

    id: Mapped[int] = mapped_column(primary_key=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
    )

    messages = relationship(
        "ChatMessage",
        back_populates="session",
    )


class ChatMessage(Base):
    __tablename__ = "chat_message"

    id: Mapped[int] = mapped_column(primary_key=True)

    session_id: Mapped[int] = mapped_column(
        ForeignKey("chat_session.id")
    )

    role: Mapped[str] = mapped_column(
        String(50)
    )

    content: Mapped[str] = mapped_column(
        Text
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
    )

    session = relationship(
        "ChatSession",
        back_populates="messages",
    )


class LeadSubmission(Base):
    __tablename__ = "lead_submission"

    id: Mapped[int] = mapped_column(primary_key=True)

    name: Mapped[str] = mapped_column(
        String(255)
    )

    email: Mapped[str] = mapped_column(
        String(255)
    )

    message: Mapped[str] = mapped_column(
        Text
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
    )


class KnowledgeDocument(Base):
    __tablename__ = "knowledge_document"

    id: Mapped[int] = mapped_column(
        primary_key=True
    )

    filename: Mapped[str] = mapped_column(
        String(500),
        unique=True,
        nullable=False,
    )

    title: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    record_id: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
    )

    category: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    tags: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    intents: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    source: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )

    dataset_version: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    metadata_json: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
    )


class KnowledgeChunk(Base):
    __tablename__ = "knowledge_chunk"

    id: Mapped[int] = mapped_column(
        primary_key=True
    )

    document_id: Mapped[int] = mapped_column(
        ForeignKey("knowledge_document.id"),
        nullable=False,
    )

    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
    )