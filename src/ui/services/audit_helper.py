"""Helper: sync audit user from NiceGUI session + decorator for handlers."""

import asyncio
import functools
from uuid import UUID


def sync_audit_user() -> None:
    """Read user_id from NiceGUI session storage and set it in the audit context.

    Call this at the top of any handler that may trigger audited mutations,
    since NiceGUI handlers run in a separate async task from page rendering.
    """
    from nicegui import app

    from src.application.services.audit_context import set_audit_user

    user_id_raw = app.storage.user.get("user_id")
    if user_id_raw:
        set_audit_user(UUID(user_id_raw))


def with_audit_user(fn):
    """Decorator that syncs the audit user before calling the handler.

    Works with both sync and async functions. Usage::

        @with_audit_user
        def _on_submit() -> None:
            ...
    """
    if asyncio.iscoroutinefunction(fn):

        @functools.wraps(fn)
        async def wrapper(*args, **kwargs):
            sync_audit_user()
            return await fn(*args, **kwargs)

    else:

        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            sync_audit_user()
            return fn(*args, **kwargs)

    return wrapper
