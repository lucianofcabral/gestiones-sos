"""EliminarGroupedClaim — soft-delete a Claim and hard-delete its GroupedClaim.

Guard: if the claim has any active Payment, deletion is blocked.
Idempotent on the Claim: calling this on an already-inactive claim is a no-op
that still returns success=True.
"""

"""EliminarGroupedClaim — soft-delete a Claim and hard-delete its GroupedClaim.

Uses UnitOfWork so both operations are atomic: if either fails, neither is
persisted.

Guard: if the claim has any active Payment, deletion is blocked.
Idempotent on the Claim: calling this on an already-inactive claim is a no-op
that still returns success=True.
"""

from uuid import UUID

from pydantic import BaseModel

from src.domain.exceptions import ClaimHasActivePaymentsError, ClaimNotFoundError
from src.domain.ports.repositories import PaymentRepoPort
from src.domain.ports.uow import UnitOfWork


# ── Input ─────────────────────────────────────────────────────────────────────


class EliminarGroupedClaimInput(BaseModel):
    claim_id: UUID


# ── Output ────────────────────────────────────────────────────────────────────


class EliminarGroupedClaimOutput(BaseModel):
    claim_id: UUID
    success: bool


# ── Use case ──────────────────────────────────────────────────────────────────


class EliminarGroupedClaim:
    """Eliminar un GroupedClaim con atomicidad vía UnitOfWork."""

    def __init__(
        self,
        uow: UnitOfWork,
        payment_repo: PaymentRepoPort | None = None,
    ) -> None:
        self._uow = uow
        self._payment_repo = payment_repo

    def execute(self, input_data: EliminarGroupedClaimInput) -> EliminarGroupedClaimOutput:
        with self._uow as uow:
            claim = uow.claims.get_by_id(input_data.claim_id)
            if claim is None:
                raise ClaimNotFoundError("Claim not found")

            # Payment guard: check for active payments before deleting
            if self._payment_repo is not None:
                payments = self._payment_repo.get_by_claim_id(input_data.claim_id)
                if any(p.active for p in payments):
                    raise ClaimHasActivePaymentsError("Claim has active payments")

            # Hard-delete the GroupedClaim record (no active field on entity)
            grouped = uow.grouped_claims.get_by_claim_id(input_data.claim_id)
            if grouped is not None:
                uow.grouped_claims.delete(grouped.grouped_claim_id)

            # Soft-delete the Claim
            uow.claims.inactivate(input_data.claim_id)

        return EliminarGroupedClaimOutput(
            claim_id=input_data.claim_id,
            success=True,
        )
