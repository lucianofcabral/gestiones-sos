import os
from logging.config import fileConfig

from dotenv import load_dotenv
from sqlalchemy import pool
from sqlalchemy import create_engine

from alembic import context

from src.infrastructure.database.tables import metadata

load_dotenv()

# Alembic Config object — acceso a alembic.ini
config = context.config

# Logging desde alembic.ini
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Le decimos a Alembic qué tablas vigilar para autogenerate
target_metadata = metadata


def _get_url() -> str:
    url = os.environ.get("DATABASE_URL")
    if not url:
        raise RuntimeError("DATABASE_URL environment variable is not set")
    return url


def run_migrations_offline() -> None:
    """Modo offline: genera SQL sin conectarse a la BD.
    Útil para revisar el SQL antes de aplicarlo."""
    context.configure(
        url=_get_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Modo online: se conecta a la BD y aplica las migraciones."""
    connectable = create_engine(_get_url(), poolclass=pool.NullPool)

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
