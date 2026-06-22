"""ObtenerFacturas — list all invoices, optionally filtered by period."""

from uuid import UUID

from src.domain.models.entities import Invoice
from src.domain.ports.repositories import BillingRepoPort


class ObtenerFacturas:
    """Return all Invoices or filter by period_id."""

    def __init__(self, billing_repo: BillingRepoPort) -> None:
        self._billing_repo = billing_repo

    def execute(self) -> list[Invoice]:
        return self._billing_repo.get_all()

    def por_periodo(self, period_id: UUID) -> list[Invoice]:
        return self._billing_repo.get_by_period_id(period_id)
