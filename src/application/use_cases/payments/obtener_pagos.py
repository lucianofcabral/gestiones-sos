"""Use case: obtener pagos (query Payments)."""

from uuid import UUID

from src.domain.models.entities import Payment
from src.domain.ports.repositories import PaymentRepoPort


class ObtenerPagos:
    """Query payments — pass-through to PaymentRepoPort."""

    def __init__(self, payment_repo: PaymentRepoPort) -> None:
        self._payment_repo = payment_repo

    def get_by_id(self, payment_id: UUID) -> Payment | None:
        """Return a payment by ID, or None."""
        return self._payment_repo.get_by_id(payment_id)

    def get_all(self) -> list[Payment]:
        """Return all payments."""
        return self._payment_repo.get_all()

    def get_by_claim_id(self, claim_id: UUID) -> list[Payment]:
        """Return payments for a given claim."""
        return self._payment_repo.get_by_claim_id(claim_id)
