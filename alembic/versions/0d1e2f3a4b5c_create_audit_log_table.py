"""create audit_log table

Tracks who changed what and when for all business entities.

Revision ID: 0d1e2f3a4b5c
Revises: 9d0e1f2a3b4c
Create Date: 2026-06-20 14:00:00.000000

"""

from typing import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0d1e2f3a4b5c"
down_revision: str | None = "9d0e1f2a3b4c"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "audit_log",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("entity_type", sa.String(50), nullable=False),
        sa.Column("entity_id", sa.UUID, nullable=False),
        sa.Column("action", sa.String(20), nullable=False),
        sa.Column("old_values", sa.JSON, nullable=True),
        sa.Column("new_values", sa.JSON, nullable=True),
        sa.Column("performed_by", sa.UUID, nullable=True),
        sa.Column(
            "created_at", sa.DateTime, nullable=False, server_default=sa.func.now()
        ),
    )


def downgrade() -> None:
    op.drop_table("audit_log")
