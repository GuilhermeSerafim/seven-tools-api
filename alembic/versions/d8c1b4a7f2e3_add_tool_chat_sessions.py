"""add tool chat sessions

Revision ID: d8c1b4a7f2e3
Revises: 782efb41d5ac
Create Date: 2026-05-25 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "d8c1b4a7f2e3"
down_revision: Union[str, None] = "782efb41d5ac"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    role_enum = sa.Enum("user", "assistant", "system", name="toolchatmessagerole")

    op.create_table(
        "tool_chat_sessions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("tool_slug", sa.String(length=120), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("archived_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_tool_chat_sessions_user_id"), "tool_chat_sessions", ["user_id"], unique=False)
    op.create_index(op.f("ix_tool_chat_sessions_tool_slug"), "tool_chat_sessions", ["tool_slug"], unique=False)
    op.create_index(
        "ix_tool_chat_sessions_user_tool_updated",
        "tool_chat_sessions",
        ["user_id", "tool_slug", "updated_at"],
        unique=False,
    )

    op.create_table(
        "tool_chat_messages",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("session_id", sa.Uuid(), nullable=False),
        sa.Column("role", role_enum, nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("attachments", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("variant", sa.String(length=50), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["session_id"], ["tool_chat_sessions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_tool_chat_messages_session_id"), "tool_chat_messages", ["session_id"], unique=False)
    op.create_index(
        "ix_tool_chat_messages_session_created",
        "tool_chat_messages",
        ["session_id", "created_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_tool_chat_messages_session_created", table_name="tool_chat_messages")
    op.drop_index(op.f("ix_tool_chat_messages_session_id"), table_name="tool_chat_messages")
    op.drop_table("tool_chat_messages")
    op.drop_index("ix_tool_chat_sessions_user_tool_updated", table_name="tool_chat_sessions")
    op.drop_index(op.f("ix_tool_chat_sessions_tool_slug"), table_name="tool_chat_sessions")
    op.drop_index(op.f("ix_tool_chat_sessions_user_id"), table_name="tool_chat_sessions")
    op.drop_table("tool_chat_sessions")
    bind = op.get_bind()
    sa.Enum("user", "assistant", "system", name="toolchatmessagerole").drop(bind, checkfirst=True)
