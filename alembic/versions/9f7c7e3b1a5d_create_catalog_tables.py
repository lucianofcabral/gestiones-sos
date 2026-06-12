"""create_catalog_tables (agents, payment_vias, claim_kinds)

Revision ID: 9f7c7e3b1a5d
Revises: c90154480bf3
Create Date: 2026-06-11 10:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import uuid


# revision identifiers, used by Alembic.
revision: str = "9f7c7e3b1a5d"
down_revision: Union[str, Sequence[str], None] = "c90154480bf3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# ── UUID v5 namespace ─────────────────────────────────────────────────────
_NS = uuid.uuid5(uuid.NAMESPACE_DNS, "sos.gestiones")


def _uuid(name: str) -> str:
    return str(uuid.uuid5(_NS, name))


def upgrade() -> None:
    op.create_table(
        "agents",
        sa.Column("agent_id", sa.UUID(), primary_key=True),
        sa.Column("name", sa.String(100), nullable=False, unique=True),
        sa.Column("active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column(
            "created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")
        ),
    )

    op.create_table(
        "payment_vias",
        sa.Column("payment_via_id", sa.UUID(), primary_key=True),
        sa.Column("name", sa.String(100), nullable=False, unique=True),
        sa.Column("active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column(
            "created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")
        ),
    )

    op.create_table(
        "claim_kinds",
        sa.Column("claim_kind_id", sa.UUID(), primary_key=True),
        sa.Column("name", sa.String(100), nullable=False, unique=True),
        sa.Column("active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column(
            "created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")
        ),
    )

    # ── Seed data: agents ───────────────────────────────────────────────────
    op.execute(
        sa.text(
            """
            INSERT INTO agents (agent_id, name) VALUES
                (:sos_id, 'SOS'),
                (:sm_id, 'SM'),
                (:asegurado_id, 'Asegurado'),
                (:prestador_id, 'Prestador'),
                (:productor_id, 'Productor'),
                (:externo_id, 'Externo')
            """
        ).bindparams(
            sos_id=_uuid("agent/SOS"),
            sm_id=_uuid("agent/SM"),
            asegurado_id=_uuid("agent/Asegurado"),
            prestador_id=_uuid("agent/Prestador"),
            productor_id=_uuid("agent/Productor"),
            externo_id=_uuid("agent/Externo"),
        )
    )

    # ── Seed data: payment_vias ─────────────────────────────────────────────
    op.execute(
        sa.text(
            """
            INSERT INTO payment_vias (payment_via_id, name) VALUES
                (:transferencia_id, 'Transferencia'),
                (:nc_id, 'Nota de Crédito'),
                (:efectivo_id, 'Efectivo'),
                (:cheque_id, 'Cheque'),
                (:cta_cte_id, 'Cta. Cte. Productor')
            """
        ).bindparams(
            transferencia_id=_uuid("payment_via/Transferencia"),
            nc_id=_uuid("payment_via/Nota de Crédito"),
            efectivo_id=_uuid("payment_via/Efectivo"),
            cheque_id=_uuid("payment_via/Cheque"),
            cta_cte_id=_uuid("payment_via/Cta. Cte. Productor"),
        )
    )

    # ── Seed data: claim_kinds ──────────────────────────────────────────────
    op.execute(
        sa.text(
            """
            INSERT INTO claim_kinds (claim_kind_id, name) VALUES
                (:sos_id, 'SOS'),
                (:tres_arroyos_id, 'Tres Arroyos'),
                (:especial_id, 'Especial')
            """
        ).bindparams(
            sos_id=_uuid("claim_kind/SOS"),
            tres_arroyos_id=_uuid("claim_kind/Tres Arroyos"),
            especial_id=_uuid("claim_kind/Especial"),
        )
    )


def downgrade() -> None:
    op.drop_table("claim_kinds")
    op.drop_table("payment_vias")
    op.drop_table("agents")
