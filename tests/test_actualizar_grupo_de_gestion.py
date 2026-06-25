"""Unit tests for ActualizarGrupoDeGestion use case.

Scenarios covered:
- Happy path: valid claim + valid group → group_id changes, commit succeeds
- Claim not found raises ClaimNotFoundError
- Group not found raises ValueError with Spanish error message
"""

from uuid import UUID, uuid4

import pytest

from src.adapters.persistence.inmemory_claim_repository import (
    InMemoryClaimRepository,
)
from src.adapters.persistence.inmemory_group_claim_repository import (
    InMemoryGroupClaimRepository,
)
from src.application.use_cases.claims.actualizar_grupo_de_gestion import (
    ActualizarGrupoDeGestion,
    ActualizarGrupoDeGestionInput,
)
from src.domain.exceptions import ClaimNotFoundError
from src.domain.models.entities import Claim, GroupClaim
from src.domain.ports.uow import UnitOfWork


# ── Fakes ─────────────────────────────────────────────────────────────────────


class FakeUnitOfWork(UnitOfWork):
    """In-memory UnitOfWork wrapping only Claim repos (no audit)."""

    def __init__(self, claims: InMemoryClaimRepository) -> None:
        self.claims = claims
        self.sos_claims = None  # type: ignore[assignment]
        self.grouped_claims = None  # type: ignore[assignment]

    def commit(self) -> None:
        pass

    def rollback(self) -> None:
        pass


# ── Fixtures ─────────────────────────────────────────────────────────────────


@pytest.fixture
def claim_repo() -> InMemoryClaimRepository:
    return InMemoryClaimRepository()


@pytest.fixture
def group_repo() -> InMemoryGroupClaimRepository:
    return InMemoryGroupClaimRepository()


@pytest.fixture
def fake_uow(claim_repo: InMemoryClaimRepository) -> FakeUnitOfWork:
    return FakeUnitOfWork(claim_repo)


@pytest.fixture
def use_case(
    fake_uow: FakeUnitOfWork,
    group_repo: InMemoryGroupClaimRepository,
) -> ActualizarGrupoDeGestion:
    return ActualizarGrupoDeGestion(uow=fake_uow, group_claim_repo=group_repo)


# ── Helpers ──────────────────────────────────────────────────────────────────


def _seed_claim(
    repo: InMemoryClaimRepository,
    *,
    group_id: UUID | None = None,
) -> Claim:
    cid = uuid4()
    claim = Claim(
        claim_id=cid,
        claim_kind_id=uuid4(),
        group_id=group_id or uuid4(),
        claimer_name="Test Claimant",
        policy_number="POL-001",
        plate="ABC-123",
    )
    repo.add(claim)
    return claim


def _seed_group(repo: InMemoryGroupClaimRepository, name: str = "Grupo A") -> GroupClaim:
    gc = GroupClaim(
        group_id=uuid4(),
        name=name,
        external_reference="EXT-001",
    )
    repo.add(gc)
    return gc


# ═══════════════════════════════════════════════════════════════════════════════
# 4.1 — Happy path
# ═══════════════════════════════════════════════════════════════════════════════


def test_actualizar_grupo_happy(
    claim_repo: InMemoryClaimRepository,
    group_repo: InMemoryGroupClaimRepository,
    use_case: ActualizarGrupoDeGestion,
) -> None:
    """Happy path: valid claim and valid group → group_id changes and output is correct."""
    old_group = _seed_group(group_repo, name="Grupo Viejo")
    new_group = _seed_group(group_repo, name="Grupo Nuevo")
    claim = _seed_claim(claim_repo, group_id=old_group.group_id)

    result = use_case.execute(
        ActualizarGrupoDeGestionInput(
            claim_id=claim.claim_id,
            new_group_id=new_group.group_id,
        )
    )

    assert result.claim_id == claim.claim_id
    assert result.old_group_id == old_group.group_id
    assert result.new_group_id == new_group.group_id
    assert result.group_name == "Grupo Nuevo"

    # Read-back verification — the claim's group_id changed in the store
    updated_claim = claim_repo.get_by_id(claim.claim_id)
    assert updated_claim is not None
    assert updated_claim.group_id == new_group.group_id


def test_actualizar_grupo_commits_on_success(
    fake_uow: FakeUnitOfWork,
    claim_repo: InMemoryClaimRepository,
    group_repo: InMemoryGroupClaimRepository,
) -> None:
    """UoW commit is called on success (ensured by __exit__ on no exception)."""
    group = _seed_group(group_repo)
    claim = _seed_claim(claim_repo, group_id=group.group_id)
    other_group = _seed_group(group_repo, name="Otro Grupo")

    uc = ActualizarGrupoDeGestion(uow=fake_uow, group_claim_repo=group_repo)
    # If UoW.__exit__ raises (due to rollback), this test fails
    result = uc.execute(
        ActualizarGrupoDeGestionInput(
            claim_id=claim.claim_id,
            new_group_id=other_group.group_id,
        )
    )
    assert result.claim_id == claim.claim_id
    assert result.new_group_id == other_group.group_id


# ═══════════════════════════════════════════════════════════════════════════════
# 4.2 — Claim not found
# ═══════════════════════════════════════════════════════════════════════════════


def test_actualizar_grupo_claim_not_found_raises(
    group_repo: InMemoryGroupClaimRepository,
    use_case: ActualizarGrupoDeGestion,
) -> None:
    """Non-existent claim raises ClaimNotFoundError."""
    group = _seed_group(group_repo)
    fake_claim_id = uuid4()

    with pytest.raises(ClaimNotFoundError, match="not found"):
        use_case.execute(
            ActualizarGrupoDeGestionInput(
                claim_id=fake_claim_id,
                new_group_id=group.group_id,
            )
        )


# ═══════════════════════════════════════════════════════════════════════════════
# 4.3 — Remove from group (new_group_id=None)
# ═══════════════════════════════════════════════════════════════════════════════


def test_actualizar_grupo_remove_from_group(
    claim_repo: InMemoryClaimRepository,
    group_repo: InMemoryGroupClaimRepository,
    use_case: ActualizarGrupoDeGestion,
) -> None:
    """new_group_id=None removes the claim from the group (sets group_id=None)."""
    group = _seed_group(group_repo)
    claim = _seed_claim(claim_repo, group_id=group.group_id)

    result = use_case.execute(
        ActualizarGrupoDeGestionInput(
            claim_id=claim.claim_id,
            new_group_id=None,
        )
    )

    assert result.claim_id == claim.claim_id
    assert result.old_group_id == group.group_id
    assert result.new_group_id is None
    assert result.group_name == ""

    # Read-back verification
    updated_claim = claim_repo.get_by_id(claim.claim_id)
    assert updated_claim is not None
    assert updated_claim.group_id is None


# ═══════════════════════════════════════════════════════════════════════════════
# 4.4 — Group not found
# ═══════════════════════════════════════════════════════════════════════════════


def test_actualizar_grupo_group_not_found_raises(
    claim_repo: InMemoryClaimRepository,
    use_case: ActualizarGrupoDeGestion,
) -> None:
    """Non-existent group raises ValueError with Spanish message."""
    claim = _seed_claim(claim_repo)

    with pytest.raises(ValueError, match="No existe un grupo"):
        use_case.execute(
            ActualizarGrupoDeGestionInput(
                claim_id=claim.claim_id,
                new_group_id=uuid4(),
            )
        )
