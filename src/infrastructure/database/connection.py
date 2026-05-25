"""
Database engine and connection management.

El engine se crea una sola vez a partir de DATABASE_URL
y se reutiliza en toda la aplicación.
"""

import os

import sqlalchemy as sa


def get_engine() -> sa.Engine:
    url = os.environ.get("DATABASE_URL")
    if not url:
        raise RuntimeError("DATABASE_URL environment variable is not set")
    return sa.create_engine(url)


# Engine singleton — creado la primera vez que se importa
_engine: sa.Engine | None = None


def engine() -> sa.Engine:
    global _engine
    if _engine is None:
        _engine = get_engine()
    return _engine


def get_connection() -> sa.Connection:
    """Context manager: úsalo con `with get_connection() as conn`."""
    return engine().connect()
