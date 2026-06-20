"""add active to invoices

active belongs on invoices (root entity) — enables soft-delete
instead of hard-delete for EliminarFactura.

Revision ID: 8c9d0e1f2a3b
Revises: 7b8e9d0f1c2a
Create Date: 2026-06-20 12:30:00.000000

"""

from typing import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "8c9d0e1f2a3b"
down_revision: str | None = "7b8e9d0f1c2a"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "invoices",
        sa.Column("active", sa.Boolean, nullable=False, server_default=sa.text("true")),
    )


def downgrade() -> None:
    op.drop_column("invoices", "active")
