"""Use case: registrar un pago (create a Payment)."""

from uuid import UUID

from pydantic import BaseModel

from src.domain.models.entities import CreditNote, Payment
from src.domain.exceptions import (
    AgentNotConfiguredError,
    InvalidNCConfigurationError,
    PeriodRequiredError,
)
from src.domain.ports.repositories import (
    AgentRepoPort,
    NcPaymentRepoPort,
    PaymentRepoPort,
    PaymentViaRepoPort,
)


# ── Input ─────────────────────────────────────────────────────────────────────


class RegistrarPagoInput(BaseModel):
    claim_id: UUID
    payer_id: UUID
    payee_id: UUID
    payment_via_id: UUID
    amount: float = 0.0
    period_id: UUID | None = None  # required when payment_via is NC


# ── Output ────────────────────────────────────────────────────────────────────


class RegistrarPagoOutput(BaseModel):
    payment_id: UUID
    success: bool = True


# ── Use case ──────────────────────────────────────────────────────────────────


class RegistrarPago:
    """Create a Payment, with NC validation when payment_via is NC.

    If the payment_via is NC (Nota de Crédito):
    - Payer MUST be SOS
    - Payee MUST be SM
    - An NcPayment (CreditNote) is also created linked to this payment.
    """

    def __init__(
        self,
        payment_repo: PaymentRepoPort,
        nc_payment_repo: NcPaymentRepoPort,
        payment_via_repo: PaymentViaRepoPort,
        agent_repo: AgentRepoPort,
    ) -> None:
        self._payment_repo = payment_repo
        self._nc_payment_repo = nc_payment_repo
        self._payment_via_repo = payment_via_repo
        self._agent_repo = agent_repo

    def execute(self, input_data: RegistrarPagoInput) -> RegistrarPagoOutput:
        """Create the payment, validating NC rules if applicable."""
        # Check if the payment_via is NC
        nc_via = self._payment_via_repo.get_nc()
        if nc_via is not None and input_data.payment_via_id == nc_via.payment_via_id:
            self._validate_nc(input_data)

        payment = self._payment_repo.add(
            Payment(
                claim_id=input_data.claim_id,
                payer_id=input_data.payer_id,
                payee_id=input_data.payee_id,
                payment_via_id=input_data.payment_via_id,
                amount=input_data.amount,
            )
        )

        # If NC, also create the NcPayment (CreditNote)
        if nc_via is not None and input_data.payment_via_id == nc_via.payment_via_id:
            if input_data.period_id is None:
                raise PeriodRequiredError("period_id is required for NC payments")
            self._nc_payment_repo.add(
                CreditNote(
                    payment_id=payment.payment_id,
                    period_id=input_data.period_id,
                )
            )

        return RegistrarPagoOutput(payment_id=payment.payment_id)

    def _validate_nc(self, input_data: RegistrarPagoInput) -> None:
        """Validate NC payment rules: payer=SOS, payee=SM."""
        sos = self._agent_repo.get_sos()
        sm = self._agent_repo.get_sm()

        if sos is None or sm is None:
            raise AgentNotConfiguredError("SOS or SM agent not configured")

        if input_data.payer_id != sos.agent_id:
            raise InvalidNCConfigurationError("NC payment must have SOS as payer")

        if input_data.payee_id != sm.agent_id:
            raise InvalidNCConfigurationError("NC payment must have SM as payee")
