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
    sa.Column("group_id", sa.UUID, nullable=True),
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
    sa.UniqueConstraint("year", "month", name="uq_periods_year_month"),
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
    sa.Column("period_id", sa.UUID, sa.ForeignKey("periods.period_id"), nullable=True),
    sa.Column("delivered", sa.Boolean, nullable=False, server_default="false"),
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

documents = sa.Table(
    "documents",
    metadata,
    sa.Column("document_id", sa.UUID, primary_key=True),
    sa.Column("hash", sa.String(64), nullable=False, unique=True),
    sa.Column("type", sa.String(100), nullable=False),
    sa.Column("name", sa.String(255), nullable=False),
    sa.Column("size", sa.Integer, nullable=False),
    sa.Column("mime", sa.String(100), nullable=False, server_default=""),
    sa.Column("description", sa.String(500), nullable=False, server_default=""),
    sa.Column("uploaded_by", sa.UUID, nullable=True),
    sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
)

document_entities = sa.Table(
    "document_entities",
    metadata,
    sa.Column("document_id", sa.UUID, nullable=False),
    sa.Column("entity_type", sa.String(50), nullable=False),
    sa.Column("entity_id", sa.UUID, nullable=False),
    sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
    sa.UniqueConstraint(
        "document_id", "entity_type", "entity_id", name="uq_doc_entity"
    ),
)

group_claims = sa.Table(
    "group_claims",
    metadata,
    sa.Column("group_id", sa.UUID, primary_key=True),
    sa.Column("name", sa.String(100), nullable=False, unique=True),
    sa.Column("external_reference", sa.String(100), nullable=False, unique=True),
    sa.Column("description", sa.String(255), nullable=True),
    sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
    sa.Column("active", sa.Boolean, nullable=False, server_default=sa.text("true")),
)

grouped_claims = sa.Table(
    "grouped_claims",
    metadata,
    sa.Column("grouped_claim_id", sa.UUID, primary_key=True),
    sa.Column(
        "claim_id", sa.UUID, sa.ForeignKey("claims.claim_id"), nullable=False
    ),
    sa.Column(
        "group_claim_id",
        sa.UUID,
        sa.ForeignKey("group_claims.group_id"),
        nullable=False,
    ),
    sa.Column("notes", sa.String(500), nullable=False, server_default=""),
    sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
)

invoices = sa.Table(
    "invoices",
    metadata,
    sa.Column("invoice_id", sa.UUID, primary_key=True),
    sa.Column("invoice_number", sa.Text, nullable=False),
    sa.Column("period_id", sa.UUID, sa.ForeignKey("periods.period_id"), nullable=False),
    sa.Column("emited_date", sa.DateTime, nullable=False),
    sa.Column("amount", sa.Numeric(12, 2), nullable=False),
    sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
    sa.Column("active", sa.Boolean, nullable=False, server_default=sa.text("true")),
)

audit_log = sa.Table(
    "audit_log",
    metadata,
    sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
    sa.Column("entity_type", sa.String(50), nullable=False),
    sa.Column("entity_id", sa.UUID, nullable=False),
    sa.Column("action", sa.String(20), nullable=False),
    sa.Column("old_values", sa.JSON, nullable=True),
    sa.Column("new_values", sa.JSON, nullable=True),
    sa.Column("performed_by", sa.UUID, sa.ForeignKey("users.user_id"), nullable=True),
    sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
)
