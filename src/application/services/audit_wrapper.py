"""AuditRepositoryWrapper — auto-log repo mutations to audit_log."""

from uuid import UUID

from src.application.services.audit_context import get_audit_user
from src.domain.models.audit_log import AuditLog
from src.domain.ports.audit import AuditRepoPort
from src.domain.ports.repositories import BaseRepo


class AuditRepositoryWrapper[T]:
    """Wraps any BaseRepo and logs mutations (update, inactivate, activate, delete) to audit.

    Fetches the entity state before mutation, computes old/new values,
    and persists an AuditLog entry via the provided AuditRepoPort.

    Unknown methods are delegated to the inner repo via __getattr__,
    so this works transparently with any repo protocol.
    """

    __slots__ = ("_inner", "_audit", "_entity_type")

    def __init__(
        self,
        inner: BaseRepo[T],
        audit_repo: AuditRepoPort,
        *,
        entity_type: str,
    ) -> None:
        object.__setattr__(self, "_inner", inner)
        object.__setattr__(self, "_audit", audit_repo)
        object.__setattr__(self, "_entity_type", entity_type)

    # ── Explicit overrides to avoid recursion via __getattr__ ────────

    def add(self, model: T) -> T:
        result = self._inner.add(model)
        self._log(
            action="create",
            entity_id=self._pluck_id(model),
            old_values=None,
            new_values=self._serialize(model),
        )
        return result

    def get_by_id(self, id: UUID) -> T | None:
        return self._inner.get_by_id(id)

    def get_all(self) -> list[T]:
        return self._inner.get_all()

    def exists(self, data: dict) -> bool:
        return self._inner.exists(data)

    def get_by_ids(self, ids: list[UUID]) -> list[T]:
        return self._inner.get_by_ids(ids)

    def update(self, id: UUID, model: T) -> bool:
        old = self._inner.get_by_id(id)
        result = self._inner.update(id, model)
        if old is not None and result:
            self._log(
                action="update",
                entity_id=id,
                old_values=self._serialize(old),
                new_values=self._serialize(model),
            )
        return result

    def delete(self, id: UUID) -> None:
        old = self._inner.get_by_id(id)
        self._inner.delete(id)
        if old is not None:
            self._log(
                action="delete",
                entity_id=id,
                old_values=self._serialize(old),
                new_values=None,
            )

    def inactivate(self, id: UUID) -> bool:
        old = self._inner.get_by_id(id)
        try:
            result = self._inner.inactivate(id)
        except AttributeError:
            return False
        if old is not None and result:
            self._log(
                action="inactivate",
                entity_id=id,
                old_values=self._serialize(old),
                new_values=None,
            )
        return result

    def activate(self, id: UUID) -> bool:
        old = self._inner.get_by_id(id)
        try:
            result = self._inner.activate(id)
        except AttributeError:
            return False
        if old is not None and result:
            self._log(
                action="activate",
                entity_id=id,
                old_values=self._serialize(old),
                new_values=None,
            )
        return result

    # ── Delegate everything else to inner (finder methods, etc.) ─────

    def __getattr__(self, name: str):
        return getattr(object.__getattribute__(self, "_inner"), name)

    # ── Helpers ──────────────────────────────────────────────────────

    def _log(
        self,
        *,
        action: str,
        entity_id: UUID,
        old_values: dict | None,
        new_values: dict | None,
    ) -> None:
        entry = AuditLog(
            entity_type=self._entity_type,
            entity_id=entity_id,
            action=action,
            old_values=old_values,
            new_values=new_values,
            performed_by=get_audit_user(),
        )
        self._audit.add(entry)

    @staticmethod
    def _serialize(model) -> dict | None:
        if model is None:
            return None
        if hasattr(model, "model_dump"):
            return model.model_dump(mode="json")
        if hasattr(model, "dict"):
            return model.dict()
        return {k: v for k, v in model.__dict__.items() if not k.startswith("_")}

    @staticmethod
    def _pluck_id(model) -> UUID:
        if hasattr(model, "model_dump"):
            raw = model.model_dump(mode="json")
            # find any field ending with _id
            for key, val in raw.items():
                if key.endswith("_id") and val is not None:
                    return UUID(val) if isinstance(val, str) else val
        return UUID(int=0)
