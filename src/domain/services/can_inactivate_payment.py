"""Domain service: determines if a Payment can be inactivated."""

from uuid import UUID

from src.domain.ports.repositories import BillingRepoPort, NcPaymentRepoPort


class CanInactivatePaymentService:
    """Determines if a payment can be inactivated based on business rules.

    A payment can be inactivated UNLESS it has an NcPayment (CreditNote)
    linked to a period that has an Invoice (period is closed).

    Returns (can_inactivate: bool, reason: str).
    """

    def __init__(
        self,
        nc_payment_repo: NcPaymentRepoPort,
        billing_repo: BillingRepoPort,
    ) -> None:
        self._nc_payment_repo = nc_payment_repo
        self._billing_repo = billing_repo

    def execute(self, payment_id: UUID) -> tuple[bool, str]:
        """Evaluate inactivation eligibility for a payment."""
        nc = self._nc_payment_repo.get_by_payment_id(payment_id)
        if nc is None:
            return (True, "No credit note associated")

        invoices = self._billing_repo.get_by_period_id(nc.period_id)
        if len(invoices) == 0:
            return (True, "Period has no invoices — not closed")

        return (False, "Cannot inactivate: credit note linked to a closed period")
