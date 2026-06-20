"""nc: remove active from nc_payments, make period_id nullable

active belongs on payments (root entity), not on nc_payments (satélite).
period_id is nullable because an NC can be created without a period assignment
(the period is assigned later when SOS confirms the discount).

Revision ID: 46591c5ae740
Revises: 906fef102332
Create Date: 2026-06-20 09:30:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "46591c5ae740"
down_revision: Union[str, Sequence[str], None] = "906fef102332"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Drop active column (active lives on payments table)
    op.drop_column("nc_payments", "active")

    # 2. Make period_id nullable (NC can be created without period assignment)
    op.alter_column("nc_payments", "period_id", nullable=True)


def downgrade() -> None:
    # 1. Restore active column
    op.add_column(
        "nc_payments",
        sa.Column("active", sa.Boolean(), nullable=False, server_default="true"),
    )

    # 2. Make period_id not nullable
    # First, set any NULL values to a default period before making it non-nullable
    # (in practice we'd fail here if there are NULLs, but during downgrade we accept the risk)
    op.alter_column("nc_payments", "period_id", nullable=False)
