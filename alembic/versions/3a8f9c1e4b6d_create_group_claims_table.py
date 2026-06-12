"""create_group_claims_table

Revision ID: 3a8f9c1e4b6d
Revises: 27fe323b1ad7
Create Date: 2026-06-12 13:30:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "3a8f9c1e4b6d"
down_revision: Union[str, Sequence[str], None] = "27fe323b1ad7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "group_claims",
        sa.Column("group_id", sa.UUID(), primary_key=True),
        sa.Column("name", sa.String(100), nullable=False, unique=True),
        sa.Column(
            "created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")
        ),
    )


def downgrade() -> None:
    op.drop_table("group_claims")
