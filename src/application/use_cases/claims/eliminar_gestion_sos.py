from uuid import UUID

from pydantic import BaseModel

from src.domain.ports.repositories import ClaimRepoPort


# ── Input ─────────────────────────────────────────────────────────────────────


class EliminarGestionSOSInput(BaseModel):
    claim_id: UUID


# ── Output ────────────────────────────────────────────────────────────────────


class EliminarGestionSOSOutput(BaseModel):
    claim_id: UUID
    success: bool


# ── Use case ──────────────────────────────────────────────────────────────────


class EliminarGestionSOS:
    """Soft-delete a Claim by setting active=False.

    Idempotent: calling this on an already-inactive claim is a no-op that
    still returns success=True.
    """

    def __init__(self, claim_repo: ClaimRepoPort) -> None:
        self._claim_repo = claim_repo

    def execute(self, input_data: EliminarGestionSOSInput) -> EliminarGestionSOSOutput:
        claim = self._claim_repo.get_by_id(input_data.claim_id)
        if claim is None:
            raise ValueError("Claim not found")

        self._claim_repo.inactivate(input_data.claim_id)

        return EliminarGestionSOSOutput(
            claim_id=input_data.claim_id,
            success=True,
        )
