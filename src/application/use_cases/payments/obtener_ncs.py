"""Use case: obtener Notas de Crédito (query CreditNotes)."""

from uuid import UUID

from src.domain.models.entities import CreditNote
from src.domain.ports.repositories import NcPaymentRepoPort


class ObtenerNotasCredito:
    """Query credit notes — pass-through to NcPaymentRepoPort."""

    def __init__(self, nc_payment_repo: NcPaymentRepoPort) -> None:
        self._nc_payment_repo = nc_payment_repo

    def get_by_id(self, nc_payment_id: UUID) -> CreditNote | None:
        """Return a credit note by ID, or None."""
        return self._nc_payment_repo.get_by_id(nc_payment_id)

    def get_all(self) -> list[CreditNote]:
        """Return all credit notes."""
        return self._nc_payment_repo.get_all()

    def get_by_payment_id(self, payment_id: UUID) -> CreditNote | None:
        """Return the credit note for a given payment, or None."""
        return self._nc_payment_repo.get_by_payment_id(payment_id)

    def get_by_period_id(self, period_id: UUID) -> list[CreditNote]:
        """Return credit notes for a given period."""
        return self._nc_payment_repo.get_by_period_id(period_id)
