"""Use case: activar una Nota de Crédito (undo soft-delete)."""

from uuid import UUID

from pydantic import BaseModel

from src.domain.ports.repositories import NcPaymentRepoPort


# ── Input ─────────────────────────────────────────────────────────────────────


class ActivarNotaCreditoInput(BaseModel):
    nc_payment_id: UUID


# ── Output ────────────────────────────────────────────────────────────────────


class ActivarNotaCreditoOutput(BaseModel):
    success: bool


# ── Use case ──────────────────────────────────────────────────────────────────


class ActivarNotaCredito:
    """Reactivate a CreditNote by setting active=True."""

    def __init__(self, nc_payment_repo: NcPaymentRepoPort) -> None:
        self._nc_payment_repo = nc_payment_repo

    def execute(self, input_data: ActivarNotaCreditoInput) -> ActivarNotaCreditoOutput:
        """Activate the credit note."""
        result = self._nc_payment_repo.activate(input_data.nc_payment_id)
        return ActivarNotaCreditoOutput(success=result)
