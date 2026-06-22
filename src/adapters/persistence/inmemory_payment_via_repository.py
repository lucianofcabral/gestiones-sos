from typing import Any
from uuid import UUID

from src.domain.models.entities import PaymentVia


class InMemoryPaymentViaRepository:
    def __init__(self) -> None:
        self._store: list[PaymentVia] = []

    # ── BaseRepo ──────────────────────────────────────────────────────────────

    def add(self, model: PaymentVia) -> PaymentVia:
        self._store.append(model)
        return model

    def get_by_id(self, id: UUID) -> PaymentVia | None:
        return next((p for p in self._store if p.payment_via_id == id), None)

    def delete(self, id: UUID) -> None:
        self._store = [p for p in self._store if p.payment_via_id != id]

    def update(self, id: UUID, model: PaymentVia) -> bool:
        for i, p in enumerate(self._store):
            if p.payment_via_id == id:
                self._store[i] = model
                return True
        return False

    def get_all(self) -> list[PaymentVia]:
        return list(self._store)

    def exists(self, data: dict[str, Any]) -> bool:
        return any(
            all(getattr(p, k) == v for k, v in data.items()) for p in self._store
        )

    def get_by_ids(self, ids: list[UUID]) -> list[PaymentVia]:
        return [p for p in self._store if p.payment_via_id in ids]

    # ── PaymentViaRepoPort ────────────────────────────────────────────────────

    def get_by_name(self, name: str) -> PaymentVia | None:
        return next((p for p in self._store if p.name == name), None)

    def get_transferencia(self) -> PaymentVia | None:
        return self.get_by_name("Transferencia")

    def get_nc(self) -> PaymentVia | None:
        return self.get_by_name("Nota de Crédito")

    # ── _Activatable ──────────────────────────────────────────────────────────

    def activate(self, id: UUID) -> bool:
        for p in self._store:
            if p.payment_via_id == id:
                p.active = True
                return True
        return False

    def inactivate(self, id: UUID) -> bool:
        for p in self._store:
            if p.payment_via_id == id:
                p.active = False
                return True
        return False
