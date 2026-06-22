"""RegistrarFactura — create a new Invoice."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from src.domain.models.entities import Invoice
from src.domain.ports.repositories import BillingRepoPort


class RegistrarFactura:
    """Create and return a new Invoice."""

    class Input(BaseModel):
        invoice_number: str
        period_id: UUID
        emited_date: datetime
        amount: float

    class Output(BaseModel):
        invoice: Invoice

    def __init__(self, billing_repo: BillingRepoPort) -> None:
        self._billing_repo = billing_repo

    def execute(self, input: Input) -> Output:
        invoice = Invoice(
            invoice_number=input.invoice_number,
            period_id=input.period_id,
            emited_date=input.emited_date,
            amount=input.amount,
        )
        created = self._billing_repo.add(invoice)
        return self.Output(invoice=created)
