from typing import Any
from uuid import UUID

from src.domain.models.entities import Claim, GroupClaim


class InMemoryGroupClaimRepository:
    """In-memory implementación de GroupClaimRepoPort para tests."""

    def __init__(self, claim_store: list[Claim] | None = None) -> None:
        self._store: list[GroupClaim] = []
        self._claim_store = claim_store if claim_store is not None else []

    # ── BaseRepo ──────────────────────────────────────────────────────────────

    def add(self, model: GroupClaim) -> GroupClaim:
        self._store.append(model)
        return model

    def get_by_id(self, id: UUID) -> GroupClaim | None:
        return next((g for g in self._store if g.group_id == id), None)

    def delete(self, id: UUID) -> None:
        self._store = [g for g in self._store if g.group_id != id]

    def update(self, id: UUID, model: GroupClaim) -> bool:
        for i, g in enumerate(self._store):
            if g.group_id == id:
                self._store[i] = model
                return True
        return False

    def get_all(self) -> list[GroupClaim]:
        return list(self._store)

    def exists(self, data: dict[str, Any]) -> bool:
        return any(
            all(getattr(g, k) == v for k, v in data.items()) for g in self._store
        )

    def get_by_ids(self, ids: list[UUID]) -> list[GroupClaim]:
        return [g for g in self._store if g.group_id in ids]

    # ── GroupClaimRepoPort ───────────────────────────────────────────────────

    def get_by_group_name(self, group_name: str) -> GroupClaim | None:
        return next((g for g in self._store if g.name == group_name), None)

    def get_by_text_like(self, text: str) -> list[GroupClaim]:
        text_lower = text.lower()
        return [g for g in self._store if text_lower in g.name.lower()]

    def get_by_claim_id(self, claim_id: UUID) -> GroupClaim | None:
        return next(
            (
                g
                for g in self._store
                if g.group_id
                in [c.group_id for c in self._claim_store if c.claim_id == claim_id]
            ),
            None,
        )

    # ── _DocReachable stubs ──────────────────────────────────────────────────

    def get_by_document_id(self, document_id: UUID) -> list[GroupClaim]:
        return []

    def get_by_document(self, document: bytes) -> list[GroupClaim]:
        return []
