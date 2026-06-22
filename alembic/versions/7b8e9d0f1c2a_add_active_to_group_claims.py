"""add active to group_claims

active belongs on group_claims (root entity) — enables soft-delete
instead of hard-delete for EliminarGrupo.

Revision ID: 7b8e9d0f1c2a
Revises: 46591c5ae740
Create Date: 2026-06-20 12:00:00.000000

"""

from typing import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "7b8e9d0f1c2a"
down_revision: str | None = "46591c5ae740"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "group_claims",
        sa.Column("active", sa.Boolean, nullable=False, server_default=sa.text("true")),
    )


def downgrade() -> None:
    op.drop_column("group_claims", "active")
