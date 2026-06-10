"""Use case: actualizar un pago (update a Payment)."""

from uuid import UUID

from pydantic import BaseModel

from src.domain.ports.repositories import PaymentRepoPort
from src.domain.services.payment_update_rules import PaymentUpdateRules


# ── Input ─────────────────────────────────────────────────────────────────────


class ActualizarPagoInput(BaseModel):
    payment_id: UUID
    payer_id: UUID | None = None
    payment_via_id: UUID | None = None
    payee_id: UUID | None = None
    amount: float | None = None


# ── Output ────────────────────────────────────────────────────────────────────


class ActualizarPagoOutput(BaseModel):
    success: bool


# ── Use case ──────────────────────────────────────────────────────────────────


class ActualizarPago:
    """Update a Payment, enforcing editability rules via PaymentUpdateRules."""

    def __init__(
        self,
        payment_repo: PaymentRepoPort,
        update_rules: PaymentUpdateRules,
    ) -> None:
        self._payment_repo = payment_repo
        self._update_rules = update_rules

    def execute(self, input_data: ActualizarPagoInput) -> ActualizarPagoOutput:
        """Attempt to update the payment."""
        payment = self._payment_repo.get_by_id(input_data.payment_id)
        if payment is None:
            return ActualizarPagoOutput(success=False)

        # Validate editability rules
        self._update_rules.validate(
            input_data.payment_id,
            payer_id=input_data.payer_id,
            payment_via_id=input_data.payment_via_id,
            payee_id=input_data.payee_id,
            amount=input_data.amount,
        )

        # Build updated payment with only the provided fields
        update_dict: dict[str, object] = {}
        for field in ("payer_id", "payment_via_id", "payee_id", "amount"):
            val = getattr(input_data, field, None)
            if val is not None:
                update_dict[field] = val

        updated = payment.model_copy(update=update_dict)
        self._payment_repo.update(input_data.payment_id, updated)

        return ActualizarPagoOutput(success=True)
