import uuid
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator

from app.modules.tool_chat.constants import ALLOWED_TOOL_SLUGS, DEFAULT_SESSION_TITLE


def validate_tool_slug(value: str) -> str:
    if value not in ALLOWED_TOOL_SLUGS:
        raise ValueError(f"Unsupported tool_slug: {value}")
    return value


class ToolChatSessionCreate(BaseModel):
    tool_slug: str
    title: str | None = Field(None, max_length=255)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("tool_slug")
    @classmethod
    def tool_slug_must_be_known(cls, value: str) -> str:
        return validate_tool_slug(value)


class ToolChatSessionPatch(BaseModel):
    title: str | None = Field(None, max_length=255)
    metadata: dict[str, Any] | None = None


class ToolChatSessionResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    tool_slug: str
    title: str
    metadata: dict[str, Any] = Field(default_factory=dict)
    archived_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class PaginatedToolChatSessionResponse(BaseModel):
    items: list[ToolChatSessionResponse]
    total: int
    page: int
    per_page: int


class ToolChatMessageCreate(BaseModel):
    role: Literal["user", "assistant", "system"]
    content: str
    payload: dict[str, Any] | None = None
    attachments: list[dict[str, Any]] | None = None
    variant: str | None = Field(None, max_length=50)


class ToolChatMessageResponse(BaseModel):
    id: uuid.UUID
    session_id: uuid.UUID
    role: Literal["user", "assistant", "system"]
    content: str
    payload: dict[str, Any] | None = None
    attachments: list[dict[str, Any]] | None = None
    variant: str | None = None
    created_at: datetime


def normalized_title(title: str | None) -> str:
    title = (title or "").strip()
    return title or DEFAULT_SESSION_TITLE
