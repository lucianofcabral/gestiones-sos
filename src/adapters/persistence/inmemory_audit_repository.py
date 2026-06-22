"""In-memory implementation of AuditRepoPort for tests."""

from uuid import UUID

from src.domain.models.audit_log import AuditLog


class InMemoryAuditRepository:
    """Stores audit entries in memory for tests."""

    def __init__(self) -> None:
        self._store: list[AuditLog] = []
        self._next_id = 1

    def add(self, entry: AuditLog) -> AuditLog:
        record = entry.model_copy(update={"id": self._next_id})
        self._next_id += 1
        self._store.append(record)
        return record

    def get_by_entity(self, entity_type: str, entity_id: UUID) -> list[AuditLog]:
        return [
            e
            for e in reversed(self._store)
            if e.entity_type == entity_type and e.entity_id == entity_id
        ]

    def get_all(self) -> list[AuditLog]:
        return list(reversed(self._store))
