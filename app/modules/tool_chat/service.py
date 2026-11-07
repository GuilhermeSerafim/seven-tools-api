import re
import uuid
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session as DbSession

from app.models.tool_chat import ToolChatMessage, ToolChatMessageRole, ToolChatSession
from app.modules.tool_chat.constants import DEFAULT_SESSION_TITLE
from app.schemas.tool_chat import (
    ToolChatMessageCreate,
    ToolChatMessageResponse,
    ToolChatSessionCreate,
    ToolChatSessionPatch,
    ToolChatSessionResponse,
    normalized_title,
)


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def serialize_utc(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def title_from_message(content: str) -> str:
    compact = re.sub(r"\s+", " ", content).strip()
    if not compact:
        return DEFAULT_SESSION_TITLE
    return compact[:80]


def serialize_session(session: ToolChatSession) -> ToolChatSessionResponse:
    return ToolChatSessionResponse(
        id=session.id,
        user_id=session.user_id,
        tool_slug=session.tool_slug,
        title=session.title,
        metadata=session.extra_metadata or {},
        archived_at=serialize_utc(session.archived_at),
        created_at=serialize_utc(session.created_at),
        updated_at=serialize_utc(session.updated_at),
    )


def serialize_message(message: ToolChatMessage) -> ToolChatMessageResponse:
    return ToolChatMessageResponse(
        id=message.id,
        session_id=message.session_id,
        role=message.role.value,
        content=message.content,
        payload=message.payload,
        attachments=message.attachments,
        variant=message.variant,
        created_at=serialize_utc(message.created_at),
    )


def create_session(
    db: DbSession,
    user_id: uuid.UUID,
    body: ToolChatSessionCreate,
) -> ToolChatSessionResponse:
    session = ToolChatSession(
        id=uuid.uuid4(),
        user_id=user_id,
        tool_slug=body.tool_slug,
        title=normalized_title(body.title),
        extra_metadata=body.metadata,
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return serialize_session(session)


def get_session(db: DbSession, user_id: uuid.UUID, session_id: uuid.UUID) -> ToolChatSession | None:
    return db.scalar(
        select(ToolChatSession).where(
            ToolChatSession.id == session_id,
            ToolChatSession.user_id == user_id,
            ToolChatSession.archived_at.is_(None),
        )
    )


def get_session_for_tool(
    db: DbSession,
    user_id: uuid.UUID,
    session_id: uuid.UUID,
    tool_slug: str,
) -> ToolChatSession | None:
    return db.scalar(
        select(ToolChatSession).where(
            ToolChatSession.id == session_id,
            ToolChatSession.user_id == user_id,
            ToolChatSession.tool_slug == tool_slug,
            ToolChatSession.archived_at.is_(None),
        )
    )


def list_sessions(
    db: DbSession,
    user_id: uuid.UUID,
    tool_slug: str,
    q: str | None,
    page: int,
    per_page: int,
) -> tuple[list[ToolChatSessionResponse], int]:
    filters = [
        ToolChatSession.user_id == user_id,
        ToolChatSession.tool_slug == tool_slug,
        ToolChatSession.archived_at.is_(None),
    ]
    if q and q.strip():
        filters.append(ToolChatSession.title.ilike(f"%{q.strip()}%"))

    total = db.scalar(select(func.count()).select_from(ToolChatSession).where(*filters)) or 0
    sessions = db.scalars(
        select(ToolChatSession)
        .where(*filters)
        .order_by(ToolChatSession.updated_at.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
    ).all()
    return [serialize_session(session) for session in sessions], total


def patch_session(
    db: DbSession,
    session: ToolChatSession,
    body: ToolChatSessionPatch,
) -> ToolChatSessionResponse:
    if body.title is not None:
        session.title = normalized_title(body.title)
    if body.metadata is not None:
        session.extra_metadata = {**(session.extra_metadata or {}), **body.metadata}
    session.updated_at = now_utc()
    db.add(session)
    db.commit()
    db.refresh(session)
    return serialize_session(session)


def list_messages(db: DbSession, session: ToolChatSession) -> list[ToolChatMessageResponse]:
    messages = db.scalars(
        select(ToolChatMessage)
        .where(ToolChatMessage.session_id == session.id)
        .order_by(ToolChatMessage.created_at.asc())
    ).all()
    return [serialize_message(message) for message in messages]


def create_message(
    db: DbSession,
    session: ToolChatSession,
    body: ToolChatMessageCreate,
) -> ToolChatMessageResponse:
    message = ToolChatMessage(
        id=uuid.uuid4(),
        session_id=session.id,
        role=ToolChatMessageRole(body.role),
        content=body.content,
        payload=body.payload,
        attachments=body.attachments,
        variant=body.variant,
    )
    db.add(message)
    if body.role == "user" and session.title == DEFAULT_SESSION_TITLE:
        session.title = title_from_message(body.content)
    session.updated_at = now_utc()
    db.add(session)
    db.commit()
    db.refresh(message)
    return serialize_message(message)
