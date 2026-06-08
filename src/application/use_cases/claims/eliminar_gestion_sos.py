from uuid import UUID

from pydantic import BaseModel

from src.domain.ports.repositories import ClaimRepoPort, PaymentRepoPort


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

    Guard: if the claim has any active Payment, deletion is blocked.
    Idempotent: calling this on an already-inactive claim is a no-op that
    still returns success=True.
    """

    def __init__(
        self, claim_repo: ClaimRepoPort, payment_repo: PaymentRepoPort | None = None
    ) -> None:
        self._claim_repo = claim_repo
        self._payment_repo = payment_repo

    def execute(self, input_data: EliminarGestionSOSInput) -> EliminarGestionSOSOutput:
        claim = self._claim_repo.get_by_id(input_data.claim_id)
        if claim is None:
            raise ValueError("Claim not found")

        # Payment guard: check for active payments before deleting
        if self._payment_repo is not None:
            payments = self._payment_repo.get_by_claim_id(input_data.claim_id)
            if any(p.active for p in payments):
                raise ValueError("Claim has active payments")

        self._claim_repo.inactivate(input_data.claim_id)

        return EliminarGestionSOSOutput(
            claim_id=input_data.claim_id,
            success=True,
        )
