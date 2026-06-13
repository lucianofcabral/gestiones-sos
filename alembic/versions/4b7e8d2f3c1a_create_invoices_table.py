"""create_invoices_table

Revision ID: 4b7e8d2f3c1a
Revises: 3a8f9c1e4b6d
Create Date: 2026-06-13 12:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "4b7e8d2f3c1a"
down_revision: Union[str, Sequence[str], None] = "3a8f9c1e4b6d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "invoices",
        sa.Column("invoice_id", sa.UUID(), primary_key=True),
        sa.Column("invoice_number", sa.Text(), nullable=False),
        sa.Column(
            "period_id",
            sa.UUID(),
            sa.ForeignKey("periods.period_id"),
            nullable=False,
        ),
        sa.Column("emited_date", sa.DateTime(), nullable=False),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")
        ),
    )


def downgrade() -> None:
    op.drop_table("invoices")
