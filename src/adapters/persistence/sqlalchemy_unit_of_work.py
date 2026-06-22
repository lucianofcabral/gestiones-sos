from src.adapters.persistence.sqlalchemy_claim_repository import (
    SqlAlchemyClaimRepository,
)
from src.adapters.persistence.sqlalchemy_grouped_claim_repository import (
    SqlAlchemyGroupedClaimRepository,
)
from src.adapters.persistence.sqlalchemy_sos_claim_repository import (
    SqlAlchemySosClaimRepository,
)
from src.adapters.persistence.sqlalchemy_audit_repository import (
    SqlAlchemyAuditRepository,
)
from src.application.services.audit_wrapper import AuditRepositoryWrapper
from src.domain.ports.uow import UnitOfWork
from src.infrastructure.database.connection import get_engine


class SqlAlchemyUnitOfWork(UnitOfWork):
    """Ejecuta múltiples operaciones de repositorio en una sola transacción.

    Si enable_audit=True, envuelve los repos con AuditRepositoryWrapper
    para registrar automáticamente create/update/inactivate/delete.
    """

    def __init__(self, enable_audit: bool = False) -> None:
        self._enable_audit = enable_audit

    def __enter__(self) -> "SqlAlchemyUnitOfWork":
        self._conn = get_engine().connect()

        raw_claims = SqlAlchemyClaimRepository(conn=self._conn)
        raw_sos = SqlAlchemySosClaimRepository(conn=self._conn)
        raw_grouped = SqlAlchemyGroupedClaimRepository(conn=self._conn)

        if self._enable_audit:
            audit_repo = SqlAlchemyAuditRepository(conn=self._conn)
            self.claims = AuditRepositoryWrapper(
                raw_claims, audit_repo, entity_type="claim"
            )
            self.sos_claims = AuditRepositoryWrapper(
                raw_sos, audit_repo, entity_type="sos_claim"
            )
            self.grouped_claims = AuditRepositoryWrapper(
                raw_grouped, audit_repo, entity_type="grouped_claim"
            )
        else:
            self.claims = raw_claims
            self.sos_claims = raw_sos
            self.grouped_claims = raw_grouped

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
