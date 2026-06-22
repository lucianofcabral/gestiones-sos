"""add_unique_constraint_on_periods_year_month

Revision ID: 5c9d8e4f2b1a
Revises: 4b7e8d2f3c1a
Create Date: 2026-06-13 12:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "5c9d8e4f2b1a"
down_revision: Union[str, Sequence[str], None] = "4b7e8d2f3c1a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_unique_constraint(
        "uq_periods_year_month", "periods", ["year", "month"]
    )


def downgrade() -> None:
    op.drop_constraint("uq_periods_year_month", "periods")
