"""Domain service: validates Payment update editability rules."""

from uuid import UUID

from src.domain.exceptions import InvalidPaymentUpdateError
from src.domain.ports.repositories import NcPaymentRepoPort, PaymentViaRepoPort


class PaymentUpdateRules:
    """Validate payment editability rules based on NC existence.

    Rules:
    - No NC exists → any field editable, but cannot change payment_via to NC.
    - NC exists   → only amount can be modified.
    """

    def __init__(
        self,
        nc_payment_repo: NcPaymentRepoPort,
        payment_via_repo: PaymentViaRepoPort,
    ) -> None:
        self._nc_payment_repo = nc_payment_repo
        self._payment_via_repo = payment_via_repo

    def validate(
        self,
        payment_id: UUID,
        payer_id: UUID | None = None,
        payment_via_id: UUID | None = None,
        payee_id: UUID | None = None,
        amount: float | None = None,
    ) -> None:
        """Raise ValueError if any editability rule is violated."""
        existing_nc = self._nc_payment_repo.get_by_payment_id(payment_id)

        if existing_nc is not None:
            # Has NC → only amount can change
            if (
                payer_id is not None
                or payment_via_id is not None
                or payee_id is not None
            ):
                raise InvalidPaymentUpdateError(
                    "Only amount can be modified when a credit note exists"
                )
        else:
            # No NC → cannot change to NC via
            if payment_via_id is not None:
                nc_via = self._payment_via_repo.get_nc()
                if nc_via is not None and payment_via_id == nc_via.payment_via_id:
                    raise InvalidPaymentUpdateError(
                        "Cannot change payment method to Credit Note"
                    )
