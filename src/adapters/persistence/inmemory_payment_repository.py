from datetime import datetime
from typing import Any
from uuid import UUID

from src.domain.models.entities import Payment


class InMemoryPaymentRepository:
    """Implementación en memoria de PaymentRepoPort para tests."""

    def __init__(self) -> None:
        self._store: list[Payment] = []

    # ── BaseRepo ──────────────────────────────────────────────────────────────

    def add(self, model: Payment) -> Payment:
        self._store.append(model)
        return model

    def get_by_id(self, id: UUID) -> Payment | None:
        return next((p for p in self._store if p.payment_id == id), None)

    def delete(self, id: UUID) -> None:
        self._store = [p for p in self._store if p.payment_id != id]

    def update(self, id: UUID, model: Payment) -> bool:
        for i, p in enumerate(self._store):
            if p.payment_id == id:
                self._store[i] = model
                return True
        return False

    def get_all(self) -> list[Payment]:
        return list(self._store)

    def exists(self, data: dict[str, Any]) -> bool:
        return any(
            all(getattr(p, k) == v for k, v in data.items()) for p in self._store
        )

    def get_by_ids(self, ids: list[UUID]) -> list[Payment]:
        return [p for p in self._store if p.payment_id in ids]

    # ── _Activatable ──────────────────────────────────────────────────────────

    def activate(self, id: UUID) -> bool:
        payment = self.get_by_id(id)
        if payment:
            return self.update(id, payment.model_copy(update={"active": True}))
        return False

    def inactivate(self, id: UUID) -> bool:
        payment = self.get_by_id(id)
        if payment:
            return self.update(id, payment.model_copy(update={"active": False}))
        return False

    # ── PaymentRepoPort extra ─────────────────────────────────────────────────

    def deleteable(self, id: UUID) -> bool:
        # Sin referencias a NcPayment en memoria: siempre permitido
        return True

    def inactivatable(self, id: UUID) -> bool:
        # Sin referencias a NcPayment en memoria: siempre permitido
        return True

    def get_by_claim_id(self, claim_id: UUID) -> list[Payment]:
        return [p for p in self._store if p.claim_id == claim_id]

    def get_by_date_range(self, start_date: str, end_date: str) -> list[Payment]:
        start = datetime.fromisoformat(start_date)
        end = datetime.fromisoformat(end_date)
        return [p for p in self._store if start <= p.created_date <= end]

    def get_by_amount_range(
        self, min_amount: float, max_amount: float
    ) -> list[Payment]:
        return [p for p in self._store if min_amount <= p.amount <= max_amount]
