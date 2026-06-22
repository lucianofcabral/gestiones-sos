"""remove active column from sos_claims

active belongs on claims (root entity), not on satélite tables.

Revision ID: 906fef102332
Revises: 6a7b8c9d0e1f
Create Date: 2026-06-20 09:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "906fef102332"
down_revision: Union[str, Sequence[str], None] = "6a7b8c9d0e1f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_column("sos_claims", "active")


def downgrade() -> None:
    op.add_column(
        "sos_claims",
        sa.Column("active", sa.Boolean(), nullable=False, server_default="true"),
    )
