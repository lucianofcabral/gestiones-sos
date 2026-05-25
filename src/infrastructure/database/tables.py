"""
SQLAlchemy Core table definitions.

Este módulo solo declara la estructura de las tablas.
No contiene lógica de negocio ni modelos de dominio.
Alembic y los repositorios PostgreSQL importan desde aquí.
"""

import sqlalchemy as sa

metadata = sa.MetaData()

users = sa.Table(
    "users",
    metadata,
    sa.Column("user_id",       sa.UUID,          primary_key=True),
    sa.Column("user_name",     sa.String(255),   nullable=False),
    sa.Column("user_email",    sa.String(255),   nullable=False, unique=True),
    sa.Column("password_hash", sa.String(255),   nullable=False),
    sa.Column("active",        sa.Boolean,       nullable=False, server_default="true"),
    sa.Column("created_at",    sa.DateTime,      nullable=False, server_default=sa.func.now()),
)
