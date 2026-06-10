"""Unit tests for EliminarGestionSOS and RegistrarGestionSOS use cases."""

from uuid import UUID, uuid4

import pytest

from src.adapters.persistence.inmemory_claim_repository import InMemoryClaimRepository
from src.adapters.persistence.inmemory_sos_claim_repository import (
    InMemorySosClaimRepository,
)
from src.application.use_cases.claims.eliminar_gestion_sos import (
    EliminarGestionSOS,
    EliminarGestionSOSInput,
)
from src.application.use_cases.claims.registrar_gestion_sos import (
    RegistrarGestionSOS,
    RegistrarGestionSOSInput,
)
from src.domain.models.entities import Claim, SosClaim
from src.domain.ports.uow import UnitOfWork


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


# ── Fakes ────────────────────────────────────────────────────────────────────


class FakeUnitOfWork(UnitOfWork):
    """In-memory UnitOfWork that wraps Claim + SosClaim repos with no-op commit/rollback."""

    def __init__(
        self,
        claims: InMemoryClaimRepository,
        sos_claims: InMemorySosClaimRepository,
    ) -> None:
        self.claims = claims
        self.sos_claims = sos_claims

    def commit(self) -> None:
        pass

    def rollback(self) -> None:
        pass


# ── RegistrarGestionSOS fixtures ─────────────────────────────────────────────


@pytest.fixture
def inmemory_sos_claim_repo() -> InMemorySosClaimRepository:
    return InMemorySosClaimRepository()


@pytest.fixture
def fake_uow(
    claim_repo: InMemoryClaimRepository,
    inmemory_sos_claim_repo: InMemorySosClaimRepository,
) -> FakeUnitOfWork:
    return FakeUnitOfWork(claim_repo, inmemory_sos_claim_repo)


@pytest.fixture
def registrar_use_case(fake_uow: FakeUnitOfWork) -> RegistrarGestionSOS:
    return RegistrarGestionSOS(fake_uow)


# ── Helpers ──────────────────────────────────────────────────────────────────


def _make_registrar_input(
    overrides: dict | None = None,
) -> RegistrarGestionSOSInput:
    data = {
        "claim_kind_id": uuid4(),
        "group_id": uuid4(),
        "claimer_name": "Juan Pérez",
        "policy_number": "POL-12345",
        "plate": "XYZ-999",
        "gestion": 1001,
        "category": "Accidente",
        "reason": "Choque frontal",
        "load_user": "admin",
        "response_user": "operador",
        "status": "Pendiente",
        "itr": 1,
    }
    if overrides:
        data.update(overrides)
    return RegistrarGestionSOSInput(**data)


# ── RegistrarGestionSOS tests ───────────────────────────────────────────────


def test_registrar_gestion_sos_happy(
    registrar_use_case: RegistrarGestionSOS,
    fake_uow: FakeUnitOfWork,
) -> None:
    """Happy path: valid input creates Claim + SosClaim, output has IDs."""
    input_data = _make_registrar_input()
    result = registrar_use_case.execute(input_data)

    # Output has IDs
    assert result.claim_id is not None
    assert result.sos_claim_id is not None

    # Read-back verification — Claim exists
    claim = fake_uow.claims.get_by_id(result.claim_id)
    assert claim is not None
    assert claim.claimer_name == input_data.claimer_name

    # Read-back verification — SosClaim exists
    sos_claim = fake_uow.sos_claims.get_by_id(result.sos_claim_id)
    assert sos_claim is not None
    assert sos_claim.gestion == input_data.gestion
    assert sos_claim.claim_id == result.claim_id


def test_registrar_duplicate_gestion_raises(
    fake_uow: FakeUnitOfWork,
) -> None:
    """Duplicate gestion number raises ValueError."""
    # Seed a SosClaim with gestion=999
    fake_uow.sos_claims.add(SosClaim(gestion=999, claim_id=uuid4()))
    use_case = RegistrarGestionSOS(fake_uow)

    input_data = _make_registrar_input(overrides={"gestion": 999})

    with pytest.raises(ValueError, match="Ya existe una gestión"):
        use_case.execute(input_data)


def test_registrar_field_roundtrip(
    registrar_use_case: RegistrarGestionSOS,
) -> None:
    """All input fields are reflected in the output DTO."""
    input_data = _make_registrar_input(
        overrides={
            "gestion": 2000,
            "claimer_name": "María García",
            "policy_number": "POL-99999",
            "plate": "ABC-456",
        }
    )
    result = registrar_use_case.execute(input_data)

    assert result.gestion == input_data.gestion
    assert result.claimer_name == input_data.claimer_name
    assert result.policy_number == input_data.policy_number
    assert result.plate == input_data.plate
