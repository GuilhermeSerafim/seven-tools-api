"""add membership validation tables

Revision ID: 9c4e7b5f2d11
Revises: 5f1c9d7a2a10
Create Date: 2026-04-10 00:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "9c4e7b5f2d11"
down_revision: Union[str, None] = "5f1c9d7a2a10"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    validation_status = postgresql.ENUM(
        "pending_review",
        "approved",
        "blocked",
        name="validationstatus",
        create_type=False,
    )
    approval_source = postgresql.ENUM(
        "seed",
        "manual",
        "clickup_email_match",
        name="approvalsource",
        create_type=False,
    )
    company_request_status = postgresql.ENUM(
        "pending",
        "resolved",
        "rejected",
        name="companyrequeststatus",
        create_type=False,
    )
    bind = op.get_bind()

    validation_status.create(bind, checkfirst=True)
    approval_source.create(bind, checkfirst=True)
    company_request_status.create(bind, checkfirst=True)

    op.add_column(
        "companies",
        sa.Column("source", sa.String(length=255), nullable=False, server_default="manual"),
    )
    op.add_column("companies", sa.Column("clickup_task_id", sa.String(length=255), nullable=True))
    op.add_column("companies", sa.Column("contact_email", sa.String(length=255), nullable=True))
    op.add_column("companies", sa.Column("partner_1_name", sa.String(length=255), nullable=True))
    op.add_column("companies", sa.Column("partner_2_name", sa.String(length=255), nullable=True))
    op.add_column("companies", sa.Column("has_contract", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column("companies", sa.Column("clickup_status", sa.String(length=255), nullable=True))
    op.add_column("companies", sa.Column("clickup_tags", sa.JSON(), nullable=True))
    op.add_column("companies", sa.Column("last_synced_at", sa.DateTime(), nullable=True))
    op.add_column("companies", sa.Column("cnpj", sa.String(length=18), nullable=True))
    op.create_unique_constraint("uq_companies_clickup_task_id", "companies", ["clickup_task_id"])
    op.create_unique_constraint("uq_companies_cnpj", "companies", ["cnpj"])

    op.add_column(
        "users",
        sa.Column("validation_status", validation_status, nullable=False, server_default="pending_review"),
    )
    op.add_column("users", sa.Column("approval_source", approval_source, nullable=True))
    op.add_column("users", sa.Column("approved_at", sa.DateTime(), nullable=True))
    op.add_column("users", sa.Column("approved_by_user_id", sa.Uuid(), nullable=True))
    op.execute(
        """
        UPDATE users
        SET validation_status = 'approved',
            approval_source = 'seed'
        """
    )
    op.create_foreign_key(
        "fk_users_approved_by_user_id_users",
        "users",
        "users",
        ["approved_by_user_id"],
        ["id"],
    )

    op.create_table(
        "company_requests",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("requested_by_user_id", sa.Uuid(), nullable=False),
        sa.Column("requested_company_name", sa.String(length=255), nullable=False),
        sa.Column("requested_cnpj", sa.String(length=18), nullable=True),
        sa.Column("status", company_request_status, nullable=False, server_default="pending"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["requested_by_user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("requested_by_user_id", name="uq_company_requests_requested_by_user_id"),
    )


def downgrade() -> None:
    op.drop_table("company_requests")

    op.drop_constraint("fk_users_approved_by_user_id_users", "users", type_="foreignkey")
    op.drop_column("users", "approved_by_user_id")
    op.drop_column("users", "approved_at")
    op.drop_column("users", "approval_source")
    op.drop_column("users", "validation_status")

    op.drop_constraint("uq_companies_cnpj", "companies", type_="unique")
    op.drop_constraint("uq_companies_clickup_task_id", "companies", type_="unique")
    op.drop_column("companies", "cnpj")
    op.drop_column("companies", "last_synced_at")
    op.drop_column("companies", "clickup_tags")
    op.drop_column("companies", "clickup_status")
    op.drop_column("companies", "has_contract")
    op.drop_column("companies", "partner_2_name")
    op.drop_column("companies", "partner_1_name")
    op.drop_column("companies", "contact_email")
    op.drop_column("companies", "clickup_task_id")
    op.drop_column("companies", "source")

    bind = op.get_bind()
    sa.Enum("pending", "resolved", "rejected", name="companyrequeststatus").drop(bind, checkfirst=True)
    sa.Enum("seed", "manual", "clickup_email_match", name="approvalsource").drop(bind, checkfirst=True)
    sa.Enum("pending_review", "approved", "blocked", name="validationstatus").drop(bind, checkfirst=True)
