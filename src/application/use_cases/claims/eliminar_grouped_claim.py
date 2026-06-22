"""EliminarGroupedClaim — soft-delete a Claim and hard-delete its GroupedClaim.

Guard: if the claim has any active Payment, deletion is blocked.
Idempotent on the Claim: calling this on an already-inactive claim is a no-op
that still returns success=True.
"""

from uuid import UUID

from pydantic import BaseModel

from src.domain.exceptions import ClaimHasActivePaymentsError, ClaimNotFoundError
from src.domain.ports.repositories import ClaimRepoPort, GroupedClaimRepoPort, PaymentRepoPort


# ── Input ─────────────────────────────────────────────────────────────────────


class EliminarGroupedClaimInput(BaseModel):
    claim_id: UUID


# ── Output ────────────────────────────────────────────────────────────────────


class EliminarGroupedClaimOutput(BaseModel):
    claim_id: UUID
    success: bool


# ── Use case ──────────────────────────────────────────────────────────────────


class EliminarGroupedClaim:
    def __init__(
        self,
        claim_repo: ClaimRepoPort,
        grouped_claim_repo: GroupedClaimRepoPort,
        payment_repo: PaymentRepoPort | None = None,
    ) -> None:
        self._claim_repo = claim_repo
        self._grouped_claim_repo = grouped_claim_repo
        self._payment_repo = payment_repo

    def execute(self, input_data: EliminarGroupedClaimInput) -> EliminarGroupedClaimOutput:
        claim = self._claim_repo.get_by_id(input_data.claim_id)
        if claim is None:
            raise ClaimNotFoundError("Claim not found")

        # Payment guard: check for active payments before deleting
        if self._payment_repo is not None:
            payments = self._payment_repo.get_by_claim_id(input_data.claim_id)
            if any(p.active for p in payments):
                raise ClaimHasActivePaymentsError("Claim has active payments")

        # Hard-delete the GroupedClaim record (no active field on entity)
        grouped = self._grouped_claim_repo.get_by_claim_id(input_data.claim_id)
        if grouped is not None:
            self._grouped_claim_repo.delete(grouped.grouped_claim_id)

        # Soft-delete the Claim
        self._claim_repo.inactivate(input_data.claim_id)

        return EliminarGroupedClaimOutput(
            claim_id=input_data.claim_id,
            success=True,
        )
