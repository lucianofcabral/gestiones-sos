"""
SQLAlchemy Core table definitions.

Este módulo solo declara la estructura de las tablas.
No contiene lógica de negocio ni modelos de dominio.
Alembic y los repositorios SQLAlchemy importan desde aquí.
"""

import sqlalchemy as sa

metadata = sa.MetaData()

users = sa.Table(
    "users",
    metadata,
    sa.Column("user_id", sa.UUID, primary_key=True),
    sa.Column("user_name", sa.String(255), nullable=False),
    sa.Column("user_email", sa.String(255), nullable=False, unique=True),
    sa.Column("password_hash", sa.String(255), nullable=False),
    sa.Column("active", sa.Boolean, nullable=False, server_default="true"),
    sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
)

claims = sa.Table(
    "claims",
    metadata,
    sa.Column("claim_id", sa.UUID, primary_key=True),
    sa.Column("claim_kind_id", sa.UUID, nullable=False),
    sa.Column("group_id", sa.UUID, nullable=False),
    sa.Column("claimer_name", sa.String(100), nullable=False),
    sa.Column("policy_number", sa.String(25), nullable=False),
    sa.Column("plate", sa.String(20), nullable=False),
    sa.Column("claimed_amount", sa.Numeric(12, 2), nullable=False, server_default="0"),
    sa.Column("comment", sa.String(255), nullable=False, server_default=""),
    sa.Column("solved", sa.Boolean, nullable=False, server_default="false"),
    sa.Column("active", sa.Boolean, nullable=False, server_default="true"),
    sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
)

periods = sa.Table(
    "periods",
    metadata,
    sa.Column("period_id", sa.UUID, primary_key=True),
    sa.Column("year", sa.Integer, nullable=False),
    sa.Column("month", sa.Integer, nullable=False),
    sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
)

sos_claims = sa.Table(
    "sos_claims",
    metadata,
    sa.Column("sos_claim_id", sa.UUID, primary_key=True),
    sa.Column("claim_id", sa.UUID, sa.ForeignKey("claims.claim_id"), nullable=False),
    sa.Column("gestion", sa.Integer, nullable=False, unique=True),
    sa.Column("category", sa.String(100), nullable=False, server_default=""),
    sa.Column("reason", sa.String(255), nullable=False, server_default=""),
    sa.Column("load_user", sa.String(100), nullable=False, server_default=""),
    sa.Column("response_user", sa.String(100), nullable=False, server_default=""),
    sa.Column("status", sa.String(50), nullable=False, server_default=""),
    sa.Column("itr", sa.Integer, nullable=False, server_default="0"),
    sa.Column("active", sa.Boolean, nullable=False, server_default="true"),
)

payments = sa.Table(
    "payments",
    metadata,
    sa.Column("payment_id", sa.UUID, primary_key=True),
    sa.Column("claim_id", sa.UUID, sa.ForeignKey("claims.claim_id"), nullable=False),
    sa.Column("payer_id", sa.UUID, nullable=False),
    sa.Column("payee_id", sa.UUID, nullable=False),
    sa.Column("payment_via_id", sa.UUID, nullable=False),
    sa.Column("amount", sa.Numeric(12, 2), nullable=False, server_default="0"),
    sa.Column("active", sa.Boolean, nullable=False, server_default="true"),
    sa.Column(
        "created_date", sa.DateTime, nullable=False, server_default=sa.func.now()
    ),
)

nc_payments = sa.Table(
    "nc_payments",
    metadata,
    sa.Column("nc_payment_id", sa.UUID, primary_key=True),
    sa.Column(
        "payment_id", sa.UUID, sa.ForeignKey("payments.payment_id"), nullable=False
    ),
    sa.Column("period_id", sa.UUID, sa.ForeignKey("periods.period_id"), nullable=False),
    sa.Column("delivered", sa.Boolean, nullable=False, server_default="false"),
    sa.Column("active", sa.Boolean, nullable=False, server_default="true"),
    sa.Column(
        "created_date", sa.DateTime, nullable=False, server_default=sa.func.now()
    ),
)

agents = sa.Table(
    "agents",
    metadata,
    sa.Column("agent_id", sa.UUID, primary_key=True),
    sa.Column("name", sa.String(100), nullable=False, unique=True),
    sa.Column("active", sa.Boolean, nullable=False, server_default="true"),
    sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
)

payment_vias = sa.Table(
    "payment_vias",
    metadata,
    sa.Column("payment_via_id", sa.UUID, primary_key=True),
    sa.Column("name", sa.String(100), nullable=False, unique=True),
    sa.Column("active", sa.Boolean, nullable=False, server_default="true"),
    sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
)

claim_kinds = sa.Table(
    "claim_kinds",
    metadata,
    sa.Column("claim_kind_id", sa.UUID, primary_key=True),
    sa.Column("name", sa.String(100), nullable=False, unique=True),
    sa.Column("active", sa.Boolean, nullable=False, server_default="true"),
    sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
)
