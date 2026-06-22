"""SQLAlchemy implementation of AuditRepoPort."""

from contextlib import contextmanager
from uuid import UUID

import sqlalchemy as sa

from src.domain.models.audit_log import AuditLog
from src.infrastructure.database.connection import get_connection
from src.infrastructure.database.tables import audit_log


class SqlAlchemyAuditRepository:
    """Persists audit log entries to PostgreSQL."""

    def __init__(self, conn: sa.Connection | None = None) -> None:
        self._conn = conn

    @contextmanager
    def _get_conn(self):
        if self._conn is not None:
            yield self._conn
        else:
            with get_connection() as c:
                yield c
                c.commit()

    def add(self, entry: AuditLog) -> AuditLog:
        with self._get_conn() as conn:
            conn.execute(
                sa.insert(audit_log).values(
                    entity_type=entry.entity_type,
                    entity_id=entry.entity_id,
                    action=entry.action,
                    old_values=entry.old_values,
                    new_values=entry.new_values,
                    performed_by=entry.performed_by,
                )
            )
        return entry

    def get_by_entity(self, entity_type: str, entity_id: UUID) -> list[AuditLog]:
        with self._get_conn() as conn:
            rows = conn.execute(
                sa.select(audit_log)
                .where(
                    sa.and_(
                        audit_log.c.entity_type == entity_type,
                        audit_log.c.entity_id == entity_id,
                    )
                )
                .order_by(audit_log.c.created_at.desc())
            ).fetchall()
        return [self._row_to_entry(r) for r in rows]

    def get_all(self) -> list[AuditLog]:
        with self._get_conn() as conn:
            rows = conn.execute(
                sa.select(audit_log).order_by(audit_log.c.created_at.desc())
            ).fetchall()
        return [self._row_to_entry(r) for r in rows]

    @staticmethod
    def _row_to_entry(row: sa.Row) -> AuditLog:
        return AuditLog(
            id=row.id,
            entity_type=row.entity_type,
            entity_id=row.entity_id,
            action=row.action,
            old_values=row.old_values,
            new_values=row.new_values,
            performed_by=row.performed_by,
            created_at=row.created_at,
        )
