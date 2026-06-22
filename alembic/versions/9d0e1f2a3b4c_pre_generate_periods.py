"""pre-generate periods from 202301 to 204012

Creates 216 periods (2023-01 through 2040-12) so the period dropdown
always has all options available without manual creation.

Revision ID: 9d0e1f2a3b4c
Revises: 8c9d0e1f2a3b
Create Date: 2026-06-20 13:00:00.000000

"""

import uuid
from typing import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "9d0e1f2a3b4c"
down_revision: str | None = "8c9d0e1f2a3b"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


_NS = uuid.uuid5(uuid.NAMESPACE_DNS, "sos.gestiones")


def _period_uuid(year: int, month: int) -> str:
    return str(uuid.uuid5(_NS, f"period/{year}-{month:02d}"))


def upgrade() -> None:
    conn = op.get_bind()
    for year in range(2023, 2041):
        for month in range(1, 13):
            conn.execute(
                sa.text(
                    """INSERT INTO periods (period_id, year, month, created_at)
                       VALUES (:pid, :year, :month, NOW())
                       ON CONFLICT (year, month) DO NOTHING"""
                ),
                {
                    "pid": _period_uuid(year, month),
                    "year": year,
                    "month": month,
                },
            )


def downgrade() -> None:
    conn = op.get_bind()
    conn.execute(
        sa.text("DELETE FROM periods WHERE year >= 2023 AND year <= 2040")
    )
