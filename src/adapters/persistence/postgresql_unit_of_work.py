import sqlalchemy as sa

from src.adapters.persistence.postgresql_claim_repository import PostgreSQLClaimRepository
from src.adapters.persistence.postgresql_sos_claim_repository import PostgreSQLSosClaimRepository
from src.domain.ports.uow import UnitOfWork
from src.infrastructure.database.connection import get_engine


class PostgreSQLUnitOfWork(UnitOfWork):
    """Ejecuta múltiples operaciones de repositorio en una sola transacción."""

    def __enter__(self) -> "PostgreSQLUnitOfWork":
        self._conn = get_engine().connect()
        self.claims = PostgreSQLClaimRepository(conn=self._conn)
        self.sos_claims = PostgreSQLSosClaimRepository(conn=self._conn)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        try:
            if exc_type:
                self._conn.rollback()
            else:
                self._conn.commit()
        finally:
            self._conn.close()

    def commit(self) -> None:
        self._conn.commit()

    def rollback(self) -> None:
        self._conn.rollback()
