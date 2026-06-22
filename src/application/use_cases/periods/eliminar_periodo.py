"""EliminarPeriodo — delete a Period by period_id with referential integrity check."""

from uuid import UUID

from pydantic import BaseModel

from src.domain.ports.repositories import (
    BillingRepoPort,
    NcPaymentRepoPort,
    PeriodRepoPort,
)


class EliminarPeriodo:
    """Delete a Period by period_id.

    Raises ValueError if the Period has associated Invoices or CreditNotes.
    Returns Output(deleted=True) on success, Output(deleted=False) if not found.
    """

    class Input(BaseModel):
        period_id: UUID

    class Output(BaseModel):
        deleted: bool

    def __init__(
        self,
        period_repo: PeriodRepoPort,
        billing_repo: BillingRepoPort,
        nc_payment_repo: NcPaymentRepoPort,
    ) -> None:
        self._period_repo = period_repo
        self._billing_repo = billing_repo
        self._nc_payment_repo = nc_payment_repo

    def execute(self, input: Input) -> Output:
        period = self._period_repo.get_by_id(input.period_id)
        if period is None:
            return self.Output(deleted=False)

        invoices = self._billing_repo.get_by_period_id(input.period_id)
        if invoices:
            raise ValueError(
                "No se puede eliminar: el período tiene facturas asociadas"
            )

        credit_notes = self._nc_payment_repo.get_by_period_id(input.period_id)
        if credit_notes:
            raise ValueError(
                "No se puede eliminar: el período tiene notas de crédito asociadas"
            )

        self._period_repo.delete(input.period_id)
        return self.Output(deleted=True)
