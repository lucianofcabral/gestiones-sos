"""Use case: marcar una Nota de Crédito como entregada."""

from uuid import UUID

from pydantic import BaseModel

from src.domain.ports.repositories import NcPaymentRepoPort


# ── Input ─────────────────────────────────────────────────────────────────────


class MarcarNotaCreditoEntregadaInput(BaseModel):
    nc_payment_id: UUID


# ── Output ────────────────────────────────────────────────────────────────────


class MarcarNotaCreditoEntregadaOutput(BaseModel):
    success: bool


# ── Use case ──────────────────────────────────────────────────────────────────


class MarcarNotaCreditoEntregada:
    """Mark a CreditNote as delivered by setting delivered=True."""

    def __init__(self, nc_payment_repo: NcPaymentRepoPort) -> None:
        self._nc_payment_repo = nc_payment_repo

    def execute(
        self, input_data: MarcarNotaCreditoEntregadaInput
    ) -> MarcarNotaCreditoEntregadaOutput:
        """Mark the credit note as delivered."""
        result = self._nc_payment_repo.mark_delivered(input_data.nc_payment_id)
        return MarcarNotaCreditoEntregadaOutput(success=result)
