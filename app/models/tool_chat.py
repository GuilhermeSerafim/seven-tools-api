import enum
import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import Enum, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class ToolChatMessageRole(str, enum.Enum):
    user = "user"
    assistant = "assistant"
    system = "system"


class ToolChatSession(Base):
    __tablename__ = "tool_chat_sessions"
    __table_args__ = (
        Index("ix_tool_chat_sessions_user_tool_updated", "user_id", "tool_slug", "updated_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), index=True)
    tool_slug: Mapped[str] = mapped_column(String(120), index=True)
    title: Mapped[str] = mapped_column(String(255), default="Novo chat")
    extra_metadata: Mapped[dict[str, Any]] = mapped_column("metadata", JSONB, default=dict)
    archived_at: Mapped[datetime | None] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(default=utc_now, onupdate=utc_now)

    messages: Mapped[list["ToolChatMessage"]] = relationship(
        back_populates="session",
        cascade="all, delete-orphan",
        order_by="ToolChatMessage.created_at",
    )


class ToolChatMessage(Base):
    __tablename__ = "tool_chat_messages"
    __table_args__ = (
        Index("ix_tool_chat_messages_session_created", "session_id", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("tool_chat_sessions.id", ondelete="CASCADE"),
        index=True,
    )
    role: Mapped[ToolChatMessageRole] = mapped_column(Enum(ToolChatMessageRole))
    content: Mapped[str] = mapped_column(Text)
    payload: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    attachments: Mapped[list[dict[str, Any]] | None] = mapped_column(JSONB, nullable=True)
    variant: Mapped[str | None] = mapped_column(String(50), nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=utc_now)

    session: Mapped[ToolChatSession] = relationship(back_populates="messages")
