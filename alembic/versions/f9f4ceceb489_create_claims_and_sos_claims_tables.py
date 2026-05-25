"""create_claims_and_sos_claims_tables

Revision ID: f9f4ceceb489
Revises: a56d9e223076
Create Date: 2026-05-25 18:10:26.864154

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f9f4ceceb489'
down_revision: Union[str, Sequence[str], None] = 'a56d9e223076'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "claims",
        sa.Column("claim_id", sa.UUID(), primary_key=True),
        sa.Column("claim_kind_id", sa.UUID(), nullable=False),
        sa.Column("group_id", sa.UUID(), nullable=False),
        sa.Column("claimer_name", sa.String(100), nullable=False),
        sa.Column("policy_number", sa.String(25), nullable=False),
        sa.Column("plate", sa.String(20), nullable=False),
        sa.Column("claimed_amount", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column("comment", sa.String(255), nullable=False, server_default=""),
        sa.Column("solved", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
    )

    op.create_table(
        "sos_claims",
        sa.Column("sos_claim_id", sa.UUID(), primary_key=True),
        sa.Column("claim_id", sa.UUID(), sa.ForeignKey("claims.claim_id"), nullable=False),
        sa.Column("gestion", sa.Integer(), nullable=False, unique=True),
        sa.Column("category", sa.String(100), nullable=False, server_default=""),
        sa.Column("reason", sa.String(255), nullable=False, server_default=""),
        sa.Column("load_user", sa.String(100), nullable=False, server_default=""),
        sa.Column("response_user", sa.String(100), nullable=False, server_default=""),
        sa.Column("status", sa.String(50), nullable=False, server_default=""),
        sa.Column("itr", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("active", sa.Boolean(), nullable=False, server_default="true"),
    )


def downgrade() -> None:
    op.drop_table("sos_claims")
    op.drop_table("claims")
