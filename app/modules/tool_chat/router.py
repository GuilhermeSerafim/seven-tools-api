import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session as DbSession

from app.dependencies import get_current_approved_user, get_db
from app.models.user import User
from app.modules.tool_chat.constants import ALLOWED_TOOL_SLUGS
from app.modules.tool_chat.service import (
    create_message,
    create_session,
    get_session_for_tool,
    get_session,
    list_messages,
    list_sessions,
    patch_session,
    serialize_session,
)
from app.schemas.tool_chat import (
    PaginatedToolChatSessionResponse,
    ToolChatMessageCreate,
    ToolChatMessageResponse,
    ToolChatSessionCreate,
    ToolChatSessionPatch,
    ToolChatSessionResponse,
)

router = APIRouter(prefix="/tool-chat", tags=["tool-chat"])


def require_known_tool_slug(tool_slug: str) -> str:
    if tool_slug not in ALLOWED_TOOL_SLUGS:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Unsupported tool_slug",
        )
    return tool_slug


def require_session(db: DbSession, user_id: uuid.UUID, session_id: uuid.UUID):
    session = get_session(db, user_id, session_id)
    if session is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tool chat session not found")
    return session


def require_session_for_tool(
    db: DbSession,
    user_id: uuid.UUID,
    session_id: uuid.UUID,
    tool_slug: str | None,
):
    if tool_slug is None:
        return require_session(db, user_id, session_id)
    require_known_tool_slug(tool_slug)
    session = get_session_for_tool(db, user_id, session_id, tool_slug)
    if session is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tool chat session not found")
    return session


@router.post("/sessions", response_model=ToolChatSessionResponse, status_code=status.HTTP_201_CREATED)
def create_one(
    body: ToolChatSessionCreate,
    user: User = Depends(get_current_approved_user),
    db: DbSession = Depends(get_db),
):
    return create_session(db, user.id, body)


@router.get("/sessions", response_model=PaginatedToolChatSessionResponse)
def list_all(
    tool_slug: str = Query(...),
    q: str | None = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(30, ge=1, le=100),
    user: User = Depends(get_current_approved_user),
    db: DbSession = Depends(get_db),
):
    require_known_tool_slug(tool_slug)
    items, total = list_sessions(db, user.id, tool_slug, q, page, per_page)
    return PaginatedToolChatSessionResponse(items=items, total=total, page=page, per_page=per_page)


@router.get("/sessions/{session_id}", response_model=ToolChatSessionResponse)
def get_one(
    session_id: uuid.UUID,
    tool_slug: str | None = Query(None),
    user: User = Depends(get_current_approved_user),
    db: DbSession = Depends(get_db),
):
    session = require_session_for_tool(db, user.id, session_id, tool_slug)
    return serialize_session(session)


@router.patch("/sessions/{session_id}", response_model=ToolChatSessionResponse)
def patch_one(
    session_id: uuid.UUID,
    body: ToolChatSessionPatch,
    user: User = Depends(get_current_approved_user),
    db: DbSession = Depends(get_db),
):
    session = require_session(db, user.id, session_id)
    return patch_session(db, session, body)


@router.get("/sessions/{session_id}/messages", response_model=list[ToolChatMessageResponse])
def list_session_messages(
    session_id: uuid.UUID,
    tool_slug: str | None = Query(None),
    user: User = Depends(get_current_approved_user),
    db: DbSession = Depends(get_db),
):
    session = require_session_for_tool(db, user.id, session_id, tool_slug)
    return list_messages(db, session)


@router.post(
    "/sessions/{session_id}/messages",
    response_model=ToolChatMessageResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_session_message(
    session_id: uuid.UUID,
    body: ToolChatMessageCreate,
    tool_slug: str | None = Query(None),
    user: User = Depends(get_current_approved_user),
    db: DbSession = Depends(get_db),
):
    session = require_session_for_tool(db, user.id, session_id, tool_slug)
    return create_message(db, session, body)
