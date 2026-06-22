from typing import Any
from uuid import UUID

from src.domain.models.entities import Invoice


class InMemoryBillingRepository:
    """In-memory implementación de BillingRepoPort para tests."""

    def __init__(self) -> None:
        self._store: list[Invoice] = []

    # ── BaseRepo ──────────────────────────────────────────────────────────────

    def add(self, model: Invoice) -> Invoice:
        self._store.append(model)
        return model

    def get_by_id(self, id: UUID) -> Invoice | None:
        return next((inv for inv in self._store if inv.invoice_id == id), None)

    def delete(self, id: UUID) -> None:
        self._store = [inv for inv in self._store if inv.invoice_id != id]

    def update(self, id: UUID, model: Invoice) -> bool:
        for i, inv in enumerate(self._store):
            if inv.invoice_id == id:
                self._store[i] = model
                return True
        return False

    def get_all(self) -> list[Invoice]:
        return list(self._store)

    def exists(self, data: dict[str, Any]) -> bool:
        return any(
            all(getattr(inv, k) == v for k, v in data.items()) for inv in self._store
        )

    def get_by_ids(self, ids: list[UUID]) -> list[Invoice]:
        return [inv for inv in self._store if inv.invoice_id in ids]

    # ── BillingRepoPort ───────────────────────────────────────────────────────

    def get_by_period_id(self, period_id: UUID) -> list[Invoice]:
        return [inv for inv in self._store if inv.period_id == period_id]

    # ── _DocReachable stubs ──────────────────────────────────────────────────

    def get_by_document_id(self, document_id: UUID) -> list[Invoice]:
        return []

    def get_by_document(self, document: bytes) -> list[Invoice]:
        return []

    # ── _Activatable ─────────────────────────────────────────────────────────

    def activate(self, id: UUID) -> bool:
        inv = self.get_by_id(id)
        if inv:
            return self.update(id, inv.model_copy(update={"active": True}))
        return False

    def inactivate(self, id: UUID) -> bool:
        inv = self.get_by_id(id)
        if inv:
            return self.update(id, inv.model_copy(update={"active": False}))
        return False
