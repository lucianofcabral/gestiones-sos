"""Domain service: determines if a Payment can be activated."""

from src.domain.models.entities import Payment
from src.domain.ports.repositories import ClaimRepoPort


class CanActivatePaymentService:
    """Check if a payment can be reactivated based on claim state.

    Returns (can_activate: bool, reason: str).
    """

    def __init__(self, claim_repo: ClaimRepoPort) -> None:
        self._claim_repo = claim_repo

    def execute(self, payment: Payment) -> tuple[bool, str]:
        """Evaluate activation eligibility for a payment."""
        claim = self._claim_repo.get_by_id(payment.claim_id)
        if claim is None:
            return (False, "Claim not found")
        if not claim.active:
            return (False, "Claim is not active — cannot reactivate payment")
        return (True, "Claim is active — payment can be reactivated")
