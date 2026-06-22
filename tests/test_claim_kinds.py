"""Unit tests for ObtenerClaimKinds use case with in-memory repository."""

from uuid import uuid4

import pytest

from src.adapters.persistence.inmemory_claim_kind_repository import (
    InMemoryClaimKindRepository,
)
from src.application.use_cases.claims.obtener_claim_kinds import ObtenerClaimKinds
from src.domain.models.entities import ClaimKind


# ═══════════════════════════════════════════════════════════════════════════════
# Fixtures
# ═══════════════════════════════════════════════════════════════════════════════


@pytest.fixture
def claim_kind_repo() -> InMemoryClaimKindRepository:
    return InMemoryClaimKindRepository()


# ═══════════════════════════════════════════════════════════════════════════════
# Seed helpers
# ═══════════════════════════════════════════════════════════════════════════════


def _seed_claim_kind(
    repo: InMemoryClaimKindRepository,
    name: str = "Test Kind",
) -> ClaimKind:
    ck = ClaimKind(claim_kind_id=uuid4(), name=name)
    repo.add(ck)
    return ck


# ═══════════════════════════════════════════════════════════════════════════════
# ObtenerClaimKinds Use Case Tests
# ═══════════════════════════════════════════════════════════════════════════════


class TestObtenerClaimKinds:
    """Tests for ObtenerClaimKinds use case."""

    def test_get_all_returns_all(
        self,
        claim_kind_repo: InMemoryClaimKindRepository,
    ) -> None:
        _seed_claim_kind(claim_kind_repo, name="Tipo A")
        _seed_claim_kind(claim_kind_repo, name="Tipo B")
        uc = ObtenerClaimKinds(claim_kind_repo)

        result = uc.execute()

        assert len(result) == 2

    def test_get_all_returns_empty(
        self,
        claim_kind_repo: InMemoryClaimKindRepository,
    ) -> None:
        uc = ObtenerClaimKinds(claim_kind_repo)

        result = uc.execute()

        assert result == []
