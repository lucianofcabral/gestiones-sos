"""Use case: inactivar un pago (soft-delete a Payment)."""

from uuid import UUID

from pydantic import BaseModel

from src.domain.ports.repositories import PaymentRepoPort
from src.domain.services.can_inactivate_payment import CanInactivatePaymentService


# ── Input ─────────────────────────────────────────────────────────────────────


class InactivarPagoInput(BaseModel):
    payment_id: UUID


# ── Output ────────────────────────────────────────────────────────────────────


class InactivarPagoOutput(BaseModel):
    payment_id: UUID
    success: bool
    reason: str = ""


# ── Use case ──────────────────────────────────────────────────────────────────


class InactivarPago:
    """Soft-delete a Payment if inactivation is allowed by business rules.

    Uses CanInactivatePaymentService to check if the payment's period is closed.
    """

    def __init__(
        self,
        payment_repo: PaymentRepoPort,
        can_inactivate_svc: CanInactivatePaymentService,
    ) -> None:
        self._payment_repo = payment_repo
        self._can_inactivate_svc = can_inactivate_svc

    def execute(self, input_data: InactivarPagoInput) -> InactivarPagoOutput:
        """Attempt to inactivate the payment."""
        payment = self._payment_repo.get_by_id(input_data.payment_id)
        if payment is None:
            return InactivarPagoOutput(
                payment_id=input_data.payment_id,
                success=False,
                reason="Payment not found",
            )

        can, reason = self._can_inactivate_svc.execute(input_data.payment_id)
        if not can:
            return InactivarPagoOutput(
                payment_id=input_data.payment_id,
                success=False,
                reason=reason,
            )

        self._payment_repo.inactivate(input_data.payment_id)

        return InactivarPagoOutput(
            payment_id=input_data.payment_id,
            success=True,
            reason=reason,
        )
