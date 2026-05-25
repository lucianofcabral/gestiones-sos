from typing import Any
from uuid import UUID

from src.domain.models.entities import Claim


class InMemoryClaimRepository:
    def __init__(self) -> None:
        self._store: list[Claim] = []

    # ── BaseRepo ──────────────────────────────────────────────────────────────

    def add(self, model: Claim) -> Claim:
        self._store.append(model)
        return model

    def get_by_id(self, id: UUID) -> Claim | None:
        return next((c for c in self._store if c.claim_id == id), None)

    def delete(self, id: UUID) -> None:
        self._store = [c for c in self._store if c.claim_id != id]

    def update(self, id: UUID, model: Claim) -> bool:
        for i, claim in enumerate(self._store):
            if claim.claim_id == id:
                self._store[i] = model
                return True
        return False

    def get_all(self) -> list[Claim]:
        return list(self._store)

    def exists(self, data: dict[str, Any]) -> bool:
        return any(
            all(getattr(c, k) == v for k, v in data.items())
            for c in self._store
        )

    def get_by_ids(self, ids: list[UUID]) -> list[Claim]:
        return [c for c in self._store if c.claim_id in ids]

    # ── _Activatable ──────────────────────────────────────────────────────────

    def activate(self, id: UUID) -> bool:
        claim = self.get_by_id(id)
        if claim:
            return self.update(id, claim.model_copy(update={"active": True}))
        return False

    def inactivate(self, id: UUID) -> bool:
        claim = self.get_by_id(id)
        if claim:
            return self.update(id, claim.model_copy(update={"active": False}))
        return False

    # ── _DocReachable ─────────────────────────────────────────────────────────

    def get_by_document_id(self, document_id: UUID) -> list[Claim]:
        # En memoria no hay tabla de relación: devuelve lista vacía
        # La implementación real usará DocumentEntity en PostgreSQL
        return []

    def get_by_document(self, document: bytes) -> list[Claim]:
        return []

    # ── ClaimRepoPort extra ───────────────────────────────────────────────────

    def get_by_text_like(self, text: str) -> Claim | None:
        text_lower = text.lower()
        return next(
            (
                c for c in self._store
                if text_lower in c.claimer_name.lower()
                or text_lower in c.policy_number.lower()
                or text_lower in c.plate.lower()
            ),
            None,
        )
