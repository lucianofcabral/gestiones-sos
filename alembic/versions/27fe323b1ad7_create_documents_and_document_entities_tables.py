"""create_documents_and_document_entities_tables

Revision ID: 27fe323b1ad7
Revises: 9f7c7e3b1a5d
Create Date: 2026-06-11 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "27fe323b1ad7"
down_revision: Union[str, Sequence[str], None] = "9f7c7e3b1a5d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "documents",
        sa.Column("document_id", sa.UUID(), primary_key=True),
        sa.Column("hash", sa.String(64), nullable=False, unique=True),
        sa.Column("type", sa.String(100), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("size", sa.Integer(), nullable=False),
        sa.Column("mime", sa.String(100), nullable=False, server_default=""),
        sa.Column("description", sa.String(500), nullable=False, server_default=""),
        sa.Column("uploaded_by", sa.UUID(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")
        ),
    )

    op.create_table(
        "document_entities",
        sa.Column("document_id", sa.UUID(), nullable=False),
        sa.Column("entity_type", sa.String(50), nullable=False),
        sa.Column("entity_id", sa.UUID(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")
        ),
        sa.UniqueConstraint("document_id", "entity_type", "entity_id", name="uq_doc_entity"),
    )


def downgrade() -> None:
    op.drop_table("document_entities")
    op.drop_table("documents")
