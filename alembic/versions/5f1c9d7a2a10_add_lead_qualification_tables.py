"""add lead qualification tables

Revision ID: 5f1c9d7a2a10
Revises: 0f98acc0313d
Create Date: 2026-04-09 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "5f1c9d7a2a10"
down_revision: Union[str, None] = "0f98acc0313d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    lead_action = sa.Enum("abordar_agora", "revisar_manualmente", "nutrir", "descartar", name="leadaction")
    lead_status = sa.Enum("novo", "em_andamento", "qualificado", "nutrir", "descartado", name="leadstatus")
    lead_tier = sa.Enum("bronze", "silver", "gold", "diamond", name="leadtier")

    op.create_table(
        "lead_qualification_configs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("company_id", sa.Uuid(), nullable=False),
        sa.Column("ideal_segments", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("ideal_company_sizes", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("ideal_roles", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("weight_segment", sa.Integer(), nullable=False),
        sa.Column("weight_company_size", sa.Integer(), nullable=False),
        sa.Column("weight_role", sa.Integer(), nullable=False),
        sa.Column("weight_urgency", sa.Integer(), nullable=False),
        sa.Column("weight_timing", sa.Integer(), nullable=False),
        sa.Column("weight_pain_level", sa.Integer(), nullable=False),
        sa.Column("bronze_max", sa.Integer(), nullable=False),
        sa.Column("silver_max", sa.Integer(), nullable=False),
        sa.Column("gold_max", sa.Integer(), nullable=False),
        sa.Column("bronze_action", lead_action, nullable=False),
        sa.Column("silver_action", lead_action, nullable=False),
        sa.Column("gold_action", lead_action, nullable=False),
        sa.Column("diamond_action", lead_action, nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("company_id", name="uq_lead_qualification_configs_company_id"),
    )

    op.create_table(
        "qualified_leads",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("company_id", sa.Uuid(), nullable=False),
        sa.Column("created_by_user_id", sa.Uuid(), nullable=False),
        sa.Column("contact_name", sa.String(length=255), nullable=False),
        sa.Column("company_name", sa.String(length=255), nullable=False),
        sa.Column("contact_role", sa.String(length=255), nullable=False),
        sa.Column("segment", sa.String(length=255), nullable=False),
        sa.Column("company_size", sa.String(length=255), nullable=False),
        sa.Column("urgency", sa.String(length=255), nullable=False),
        sa.Column("timing", sa.String(length=255), nullable=False),
        sa.Column("pain_level", sa.String(length=255), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("status", lead_status, nullable=False),
        sa.Column("score", sa.Integer(), nullable=False),
        sa.Column("tier", lead_tier, nullable=False),
        sa.Column("recommended_action", lead_action, nullable=False),
        sa.Column("scoring_snapshot", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"]),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_qualified_leads_company_id"), "qualified_leads", ["company_id"], unique=False)
    op.create_index(op.f("ix_qualified_leads_created_by_user_id"), "qualified_leads", ["created_by_user_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_qualified_leads_created_by_user_id"), table_name="qualified_leads")
    op.drop_index(op.f("ix_qualified_leads_company_id"), table_name="qualified_leads")
    op.drop_table("qualified_leads")
    op.drop_table("lead_qualification_configs")
    bind = op.get_bind()
    sa.Enum("abordar_agora", "revisar_manualmente", "nutrir", "descartar", name="leadaction").drop(bind, checkfirst=True)
    sa.Enum("novo", "em_andamento", "qualificado", "nutrir", "descartado", name="leadstatus").drop(bind, checkfirst=True)
    sa.Enum("bronze", "silver", "gold", "diamond", name="leadtier").drop(bind, checkfirst=True)
