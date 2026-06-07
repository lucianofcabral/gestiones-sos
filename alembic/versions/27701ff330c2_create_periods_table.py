"""create_periods_table

Revision ID: 27701ff330c2
Revises: f9f4ceceb489
Create Date: 2026-06-07 12:40:05.407112

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "27701ff330c2"
down_revision: Union[str, Sequence[str], None] = "f9f4ceceb489"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "periods",
        sa.Column("period_id", sa.UUID(), primary_key=True),
        sa.Column("year", sa.Integer(), nullable=False),
        sa.Column("month", sa.Integer(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")
        ),
    )


def downgrade() -> None:
    op.drop_table("periods")
