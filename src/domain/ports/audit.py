"""AuditRepoPort — abstraction for writing audit log entries."""

from typing import Protocol
from uuid import UUID

from src.domain.models.audit_log import AuditLog


class AuditRepoPort(Protocol):
    """Port for persisting audit log entries."""

    def add(self, entry: AuditLog) -> AuditLog:
        """Persist an audit entry and return it with id populated."""
        ...

    def get_by_entity(self, entity_type: str, entity_id: UUID) -> list[AuditLog]:
        """Retrieve all audit entries for a given entity."""
        ...

    def get_all(self) -> list[AuditLog]:
        """Retrieve all audit entries, newest first."""
        ...
