from typing import Any
from uuid import UUID

from src.domain.models.entities import CreditNote


class InMemoryNcPaymentRepository:
    """Implementación en memoria de NcPaymentRepoPort para tests."""

    def __init__(self) -> None:
        self._store: list[CreditNote] = []

    # ── BaseRepo ──────────────────────────────────────────────────────────────

    def add(self, model: CreditNote) -> CreditNote:
        self._store.append(model)
        return model

    def get_by_id(self, id: UUID) -> CreditNote | None:
        return next((n for n in self._store if n.nc_payment_id == id), None)

    def delete(self, id: UUID) -> None:
        self._store = [n for n in self._store if n.nc_payment_id != id]

    def update(self, id: UUID, model: CreditNote) -> bool:
        for i, n in enumerate(self._store):
            if n.nc_payment_id == id:
                self._store[i] = model
                return True
        return False

    def get_all(self) -> list[CreditNote]:
        return list(self._store)

    def exists(self, data: dict[str, Any]) -> bool:
        return any(
            all(getattr(n, k) == v for k, v in data.items()) for n in self._store
        )

    def get_by_ids(self, ids: list[UUID]) -> list[CreditNote]:
        return [n for n in self._store if n.nc_payment_id in ids]

    # ── _Activatable ──────────────────────────────────────────────────────────

    def activate(self, id: UUID) -> bool:
        note = self.get_by_id(id)
        if note:
            return self.update(id, note.model_copy(update={"active": True}))
        return False

    def inactivate(self, id: UUID) -> bool:
        note = self.get_by_id(id)
        if note:
            return self.update(id, note.model_copy(update={"active": False}))
        return False

    # ── NcPaymentRepoPort extra ───────────────────────────────────────────────

    def deleteable(self, id: UUID) -> bool:
        return True

    def mark_delivered(self, id: UUID) -> bool:
        note = self.get_by_id(id)
        if note:
            return self.update(id, note.model_copy(update={"delivered": True}))
        return False

    def get_by_payment_id(self, payment_id: UUID) -> CreditNote | None:
        return next((n for n in self._store if n.payment_id == payment_id), None)

    def get_by_period_id(self, period_id: UUID) -> list[CreditNote]:
        return [n for n in self._store if n.period_id == period_id]
