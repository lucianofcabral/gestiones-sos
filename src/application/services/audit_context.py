"""Audit context — set the current user for audit logging."""

import contextvars
from uuid import UUID

_current_user_id: contextvars.ContextVar[UUID | None] = contextvars.ContextVar(
    "audit_user_id", default=None
)


def set_audit_user(user_id: UUID | None) -> None:
    """Set the current user for the duration of a request."""
    _current_user_id.set(user_id)


def get_audit_user() -> UUID | None:
    """Get the current user, if any."""
    return _current_user_id.get()
