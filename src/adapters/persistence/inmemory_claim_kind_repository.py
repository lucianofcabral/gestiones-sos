from typing import Any
from uuid import UUID

from src.domain.models.entities import ClaimKind


class InMemoryClaimKindRepository:
    def __init__(self) -> None:
        self._store: list[ClaimKind] = []

    # ── BaseRepo ──────────────────────────────────────────────────────────────

    def add(self, model: ClaimKind) -> ClaimKind:
        self._store.append(model)
        return model

    def get_by_id(self, id: UUID) -> ClaimKind | None:
        return next((c for c in self._store if c.claim_kind_id == id), None)

    def delete(self, id: UUID) -> None:
        self._store = [c for c in self._store if c.claim_kind_id != id]

    def update(self, id: UUID, model: ClaimKind) -> bool:
        for i, c in enumerate(self._store):
            if c.claim_kind_id == id:
                self._store[i] = model
                return True
        return False

    def get_all(self) -> list[ClaimKind]:
        return list(self._store)

    def exists(self, data: dict[str, Any]) -> bool:
        return any(
            all(getattr(c, k) == v for k, v in data.items()) for c in self._store
        )

    def get_by_ids(self, ids: list[UUID]) -> list[ClaimKind]:
        return [c for c in self._store if c.claim_kind_id in ids]

    # ── ClaimKindRepoPort ─────────────────────────────────────────────────────

    def get_by_name(self, name: str) -> ClaimKind | None:
        return next((c for c in self._store if c.name == name), None)

    # ── _Activatable ──────────────────────────────────────────────────────────

    def activate(self, id: UUID) -> bool:
        for c in self._store:
            if c.claim_kind_id == id:
                c.active = True
                return True
        return False

    def inactivate(self, id: UUID) -> bool:
        for c in self._store:
            if c.claim_kind_id == id:
                c.active = False
                return True
        return False
