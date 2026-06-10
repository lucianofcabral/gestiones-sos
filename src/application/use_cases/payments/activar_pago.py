"""Use case: activar un pago (reactivate a Payment)."""

from uuid import UUID

from pydantic import BaseModel

from src.domain.ports.repositories import PaymentRepoPort
from src.domain.services.can_activate_payment import CanActivatePaymentService


# ── Input ─────────────────────────────────────────────────────────────────────


class ActivarPagoInput(BaseModel):
    payment_id: UUID


# ── Output ────────────────────────────────────────────────────────────────────


class ActivarPagoOutput(BaseModel):
    payment_id: UUID
    success: bool
    reason: str = ""


# ── Use case ──────────────────────────────────────────────────────────────────


class ActivarPago:
    """Reactivate a soft-deleted Payment if the claim is active."""

    def __init__(
        self,
        payment_repo: PaymentRepoPort,
        can_activate_svc: CanActivatePaymentService,
    ) -> None:
        self._payment_repo = payment_repo
        self._can_activate_svc = can_activate_svc

    def execute(self, input_data: ActivarPagoInput) -> ActivarPagoOutput:
        """Attempt to reactivate the payment."""
        payment = self._payment_repo.get_by_id(input_data.payment_id)
        if payment is None:
            return ActivarPagoOutput(
                payment_id=input_data.payment_id,
                success=False,
                reason="Payment not found",
            )

        can, reason = self._can_activate_svc.execute(payment)
        if not can:
            return ActivarPagoOutput(
                payment_id=input_data.payment_id,
                success=False,
                reason=reason,
            )

        self._payment_repo.activate(input_data.payment_id)

        return ActivarPagoOutput(
            payment_id=input_data.payment_id,
            success=True,
            reason=reason,
        )
