"""In-memory GroupedClaimRepoPort for tests."""

from typing import Any
from uuid import UUID

from src.domain.models.entities import GroupedClaim


class InMemoryGroupedClaimRepository:
    """In-memory implementation of GroupedClaimRepoPort for tests."""

    def __init__(self) -> None:
        self._store: list[GroupedClaim] = []

    # ── BaseRepo ──────────────────────────────────────────────────────────────

    def add(self, model: GroupedClaim) -> GroupedClaim:
        self._store.append(model)
        return model

    def get_by_id(self, id: UUID) -> GroupedClaim | None:
        return next((g for g in self._store if g.grouped_claim_id == id), None)

    def delete(self, id: UUID) -> None:
        self._store = [g for g in self._store if g.grouped_claim_id != id]

    def update(self, id: UUID, model: GroupedClaim) -> bool:
        for i, g in enumerate(self._store):
            if g.grouped_claim_id == id:
                self._store[i] = model
                return True
        return False

    def get_all(self) -> list[GroupedClaim]:
        return list(self._store)

    def exists(self, data: dict[str, Any]) -> bool:
        return any(
            all(getattr(g, k) == v for k, v in data.items()) for g in self._store
        )

    def get_by_ids(self, ids: list[UUID]) -> list[GroupedClaim]:
        return [g for g in self._store if g.grouped_claim_id in ids]

    # ── GroupedClaimRepoPort extra ────────────────────────────────────────────

    def get_by_claim_id(self, claim_id: UUID) -> GroupedClaim | None:
        return next(
            (g for g in self._store if g.claim_id == claim_id),
            None,
        )
