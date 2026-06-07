from typing import Any
from uuid import UUID

from src.domain.models.entities import Period


class InMemoryPeriodRepository:
    def __init__(self) -> None:
        self._store: list[Period] = []

    # ── BaseRepo ──────────────────────────────────────────────────────────────

    def add(self, model: Period) -> Period:
        self._store.append(model)
        return model

    def get_by_id(self, id: UUID) -> Period | None:
        return next((p for p in self._store if p.period_id == id), None)

    def delete(self, id: UUID) -> None:
        self._store = [p for p in self._store if p.period_id != id]

    def update(self, id: UUID, model: Period) -> bool:
        for i, period in enumerate(self._store):
            if period.period_id == id:
                self._store[i] = model
                return True
        return False

    def get_all(self) -> list[Period]:
        return list(self._store)

    def exists(self, data: dict[str, Any]) -> bool:
        return any(
            all(getattr(p, k) == v for k, v in data.items()) for p in self._store
        )

    def get_by_ids(self, ids: list[UUID]) -> list[Period]:
        return [p for p in self._store if p.period_id in ids]

    # ── PeriodRepoPort ────────────────────────────────────────────────────────

    def get_by_year_month(self, year: int, month: int) -> Period | None:
        return next(
            (p for p in self._store if p.year == year and p.month == month), None
        )

    def get_n_last(self, n: int | None) -> list[Period]:
        sorted_periods = sorted(
            self._store,
            key=lambda p: (p.year, p.month),
            reverse=True,
        )
        if n is None:
            return sorted_periods
        return sorted_periods[:n]

    def get_total_billing_by_year_month(self, year: int, month: int) -> float:
        raise NotImplementedError(
            "get_total_billing_by_year_month requiere el módulo Billing"
        )
