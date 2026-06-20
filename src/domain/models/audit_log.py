"""AuditLog — immutable record of a business entity mutation."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class AuditLog(BaseModel):
    """Immutable record tracking who changed what and when."""

    id: int | None = None
    entity_type: str
    entity_id: UUID
    action: str  # create, update, inactivate, activate, delete
    old_values: dict | None = None
    new_values: dict | None = None
    performed_by: UUID | None = None
    created_at: datetime | None = None
