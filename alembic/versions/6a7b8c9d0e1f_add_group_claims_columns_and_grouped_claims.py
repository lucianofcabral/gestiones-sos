"""add group_claims columns and grouped_claims table

Revision ID: 6a7b8c9d0e1f
Revises: 5c9d8e4f2b1a
Create Date: 2026-06-15 10:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "6a7b8c9d0e1f"
down_revision: Union[str, Sequence[str], None] = "5c9d8e4f2b1a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Step 1: ADD columns as nullable first
    op.add_column(
        "group_claims",
        sa.Column("external_reference", sa.String(100), nullable=True),
    )
    op.add_column(
        "group_claims",
        sa.Column("description", sa.String(255), nullable=True),
    )

    # Step 2: Backfill existing rows — external_reference = name
    op.execute(
        "UPDATE group_claims SET external_reference = name "
        "WHERE external_reference IS NULL"
    )

    # Step 3: Set NOT NULL and UNIQUE on external_reference
    op.alter_column("group_claims", "external_reference", nullable=False)
    op.create_unique_constraint(
        "uq_group_claims_external_reference",
        "group_claims",
        ["external_reference"],
    )

    # Step 4: CREATE grouped_claims table
    op.create_table(
        "grouped_claims",
        sa.Column("grouped_claim_id", sa.UUID(), primary_key=True),
        sa.Column("claim_id", sa.UUID(), sa.ForeignKey("claims.claim_id"), nullable=False),
        sa.Column("group_claim_id", sa.UUID(), sa.ForeignKey("group_claims.group_id"), nullable=False),
        sa.Column("notes", sa.String(500), nullable=False, server_default=""),
        sa.Column(
            "created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")
        ),
    )


def downgrade() -> None:
    op.drop_table("grouped_claims")
    op.drop_constraint("uq_group_claims_external_reference", "group_claims")
    op.drop_column("group_claims", "description")
    op.drop_column("group_claims", "external_reference")
