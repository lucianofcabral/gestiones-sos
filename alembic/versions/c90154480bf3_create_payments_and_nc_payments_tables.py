"""create_payments_and_nc_payments_tables

Revision ID: c90154480bf3
Revises: 27701ff330c2
Create Date: 2026-06-07 13:04:01.710205

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "c90154480bf3"
down_revision: Union[str, Sequence[str], None] = "27701ff330c2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "payments",
        sa.Column("payment_id", sa.UUID(), primary_key=True),
        sa.Column("claim_id", sa.UUID(), sa.ForeignKey("claims.claim_id"), nullable=False),
        sa.Column("payer_id", sa.UUID(), nullable=False),
        sa.Column("payee_id", sa.UUID(), nullable=False),
        sa.Column("payment_via_id", sa.UUID(), nullable=False),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column("active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_date", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
    )

    op.create_table(
        "nc_payments",
        sa.Column("nc_payment_id", sa.UUID(), primary_key=True),
        sa.Column("payment_id", sa.UUID(), sa.ForeignKey("payments.payment_id"), nullable=False),
        sa.Column("period_id", sa.UUID(), sa.ForeignKey("periods.period_id"), nullable=False),
        sa.Column("delivered", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_date", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
    )


def downgrade() -> None:
    op.drop_table("nc_payments")
    op.drop_table("payments")
