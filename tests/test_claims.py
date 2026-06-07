"""Unit tests for EliminarGestionSOS use case using InMemoryClaimRepository."""

from uuid import UUID, uuid4

import pytest

from src.adapters.persistence.inmemory_claim_repository import InMemoryClaimRepository
from src.application.use_cases.claims.eliminar_gestion_sos import (
    EliminarGestionSOS,
    EliminarGestionSOSInput,
)
from src.domain.models.entities import Claim


# ── Fixtures ─────────────────────────────────────────────────────────────────


@pytest.fixture
def claim_repo() -> InMemoryClaimRepository:
    return InMemoryClaimRepository()


# ── Helpers ──────────────────────────────────────────────────────────────────


def _seed_claim(repo: InMemoryClaimRepository, claim_id: UUID | None = None) -> Claim:
    cid = claim_id or uuid4()
    claim = Claim(
        claim_id=cid,
        claim_kind_id=uuid4(),
        group_id=uuid4(),
        claimer_name="Test Claimant",
        policy_number="POL-001",
        plate="ABC-123",
    )
    repo.add(claim)
    return claim


# ── Happy path ───────────────────────────────────────────────────────────────


def test_delete_existing_claim_sets_active_false(
    claim_repo: InMemoryClaimRepository,
) -> None:
    """Happy path: deleting an existing claim sets active=False."""
    claim = _seed_claim(claim_repo)
    use_case = EliminarGestionSOS(claim_repo)

    result = use_case.execute(EliminarGestionSOSInput(claim_id=claim.claim_id))

    assert result.success is True
    assert result.claim_id == claim.claim_id

    # Read-back verification — proves the repo was actually called
    updated = claim_repo.get_by_id(claim.claim_id)
    assert updated is not None
    assert updated.active is False


# ── Not found ────────────────────────────────────────────────────────────────


def test_delete_nonexistent_claim_raises_value_error(
    claim_repo: InMemoryClaimRepository,
) -> None:
    """Not found: calling with a random UUID raises ValueError."""
    use_case = EliminarGestionSOS(claim_repo)
    fake_id = uuid4()

    with pytest.raises(ValueError, match="not found"):
        use_case.execute(EliminarGestionSOSInput(claim_id=fake_id))


# ── Idempotent ───────────────────────────────────────────────────────────────


def test_delete_idempotent(claim_repo: InMemoryClaimRepository) -> None:
    """Idempotent: deleting an already inactive claim succeeds (no-op)."""
    claim = _seed_claim(claim_repo)
    use_case = EliminarGestionSOS(claim_repo)

    # First delete
    result1 = use_case.execute(EliminarGestionSOSInput(claim_id=claim.claim_id))
    assert result1.success is True
    assert result1.claim_id == claim.claim_id

    # Verify inactive after first delete
    updated = claim_repo.get_by_id(claim.claim_id)
    assert updated is not None
    assert updated.active is False

    # Second delete — idempotent, should also succeed
    result2 = use_case.execute(EliminarGestionSOSInput(claim_id=claim.claim_id))
    assert result2.success is True
    assert result2.claim_id == claim.claim_id

    # Verify still inactive
    updated2 = claim_repo.get_by_id(claim.claim_id)
    assert updated2 is not None
    assert updated2.active is False
