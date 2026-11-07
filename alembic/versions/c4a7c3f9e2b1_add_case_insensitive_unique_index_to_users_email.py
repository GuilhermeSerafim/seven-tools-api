"""add case insensitive unique index to users email

Revision ID: c4a7c3f9e2b1
Revises: 9c4e7b5f2d11
Create Date: 2026-04-10 00:00:01.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "c4a7c3f9e2b1"
down_revision: Union[str, None] = "9c4e7b5f2d11"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    duplicate_rows = bind.execute(
        sa.text(
            """
            SELECT lower(email) AS normalized_email,
                   array_agg(email ORDER BY email) AS emails
            FROM users
            GROUP BY lower(email)
            HAVING COUNT(*) > 1
            """
        )
    ).fetchall()

    if duplicate_rows:
        duplicate_details = "; ".join(
            f"{row.normalized_email}: {', '.join(row.emails)}"
            for row in duplicate_rows
        )
        raise RuntimeError(
            "Cannot create case-insensitive unique index on users.email because duplicate "
            f"normalized emails already exist: {duplicate_details}"
        )

    op.create_index(
        "uq_users_email_lower",
        "users",
        [sa.text("lower(email)")],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("uq_users_email_lower", table_name="users")
