"""ObtenerFactura — get a single Invoice by ID."""

from uuid import UUID

from src.domain.models.entities import Invoice
from src.domain.ports.repositories import BillingRepoPort


class ObtenerFactura:
    """Return an Invoice by invoice_id, or None if not found."""

    def __init__(self, billing_repo: BillingRepoPort) -> None:
        self._billing_repo = billing_repo

    def execute(self, invoice_id: UUID) -> Invoice | None:
        return self._billing_repo.get_by_id(invoice_id)
