"""Use case: registrar una Nota de Crédito (create an NcPayment)."""

from uuid import UUID

from pydantic import BaseModel

from src.domain.models.entities import CreditNote
from src.domain.ports.repositories import NcPaymentRepoPort


# ── Input ─────────────────────────────────────────────────────────────────────


class RegistrarNotaCreditoInput(BaseModel):
    payment_id: UUID
    period_id: UUID
    delivered: bool = False


# ── Output ────────────────────────────────────────────────────────────────────


class RegistrarNotaCreditoOutput(BaseModel):
    nc_payment_id: UUID
    success: bool = True


# ── Use case ──────────────────────────────────────────────────────────────────


class RegistrarNotaCredito:
    """Create an NcPayment (CreditNote) linked to a payment and period."""

    def __init__(self, nc_payment_repo: NcPaymentRepoPort) -> None:
        self._nc_payment_repo = nc_payment_repo

    def execute(
        self, input_data: RegistrarNotaCreditoInput
    ) -> RegistrarNotaCreditoOutput:
        """Create and persist the CreditNote."""
        nc = self._nc_payment_repo.add(
            CreditNote(
                payment_id=input_data.payment_id,
                period_id=input_data.period_id,
                delivered=input_data.delivered,
            )
        )
        return RegistrarNotaCreditoOutput(nc_payment_id=nc.nc_payment_id)
