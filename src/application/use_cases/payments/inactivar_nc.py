"""Use case: inactivar una Nota de Crédito (soft-delete)."""

from uuid import UUID

from pydantic import BaseModel

from src.domain.ports.repositories import NcPaymentRepoPort


# ── Input ─────────────────────────────────────────────────────────────────────


class InactivarNotaCreditoInput(BaseModel):
    nc_payment_id: UUID


# ── Output ────────────────────────────────────────────────────────────────────


class InactivarNotaCreditoOutput(BaseModel):
    success: bool


# ── Use case ──────────────────────────────────────────────────────────────────


class InactivarNotaCredito:
    """Soft-delete a CreditNote by setting active=False."""

    def __init__(self, nc_payment_repo: NcPaymentRepoPort) -> None:
        self._nc_payment_repo = nc_payment_repo

    def execute(
        self, input_data: InactivarNotaCreditoInput
    ) -> InactivarNotaCreditoOutput:
        """Inactivate the credit note."""
        result = self._nc_payment_repo.inactivate(input_data.nc_payment_id)
        return InactivarNotaCreditoOutput(success=result)
