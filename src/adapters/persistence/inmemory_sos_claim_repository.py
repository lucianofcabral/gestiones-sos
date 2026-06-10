from typing import Any
from uuid import UUID

from src.domain.models.entities import SosClaim


class InMemorySosClaimRepository:
    def __init__(self) -> None:
        self._store: list[SosClaim] = []

    # ── BaseRepo ──────────────────────────────────────────────────────────────

    def add(self, model: SosClaim) -> SosClaim:
        self._store.append(model)
        return model

    def get_by_id(self, id: UUID) -> SosClaim | None:
        return next((s for s in self._store if s.sos_claim_id == id), None)

    def delete(self, id: UUID) -> None:
        self._store = [s for s in self._store if s.sos_claim_id != id]

    def update(self, id: UUID, model: SosClaim) -> bool:
        for i, sos_claim in enumerate(self._store):
            if sos_claim.sos_claim_id == id:
                self._store[i] = model
                return True
        return False

    def get_all(self) -> list[SosClaim]:
        return list(self._store)

    def exists(self, data: dict[str, Any]) -> bool:
        return any(
            all(getattr(s, k) == v for k, v in data.items()) for s in self._store
        )

    def get_by_ids(self, ids: list[UUID]) -> list[SosClaim]:
        return [s for s in self._store if s.sos_claim_id in ids]

    # ── _Activatable ──────────────────────────────────────────────────────────

    def activate(self, id: UUID) -> bool:
        # SosClaim doesn't have an `active` field; no-op for protocol compat
        return self.get_by_id(id) is not None

    def inactivate(self, id: UUID) -> bool:
        # SosClaim doesn't have an `active` field; no-op for protocol compat
        return self.get_by_id(id) is not None

    # ── SosClaimRepoPort extra ────────────────────────────────────────────────

    def get_by_number(self, claim_number: int) -> SosClaim | None:
        return next(
            (s for s in self._store if s.gestion == claim_number),
            None,
        )

    def get_claims_by_claim_id(self, claim_id: UUID) -> list[SosClaim]:
        return [s for s in self._store if s.claim_id == claim_id]

    def get_by_status(self, status: str) -> list[SosClaim]:
        return [s for s in self._store if s.status == status]

    def get_by_text_like(self, text: str) -> SosClaim | None:
        text_lower = text.lower()
        return next(
            (
                s
                for s in self._store
                if text_lower in s.category.lower()
                or text_lower in s.reason.lower()
                or text_lower in s.load_user.lower()
                or text_lower in s.response_user.lower()
                or text_lower in s.status.lower()
            ),
            None,
        )
