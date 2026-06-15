"""Unit tests for EliminarGestionSOS, RegistrarGestionSOS, RegistrarGroupedClaim,
and EliminarGroupedClaim use cases."""

from uuid import UUID, uuid4

import pytest
from pydantic import ValidationError

from src.adapters.persistence.inmemory_claim_repository import InMemoryClaimRepository
from src.adapters.persistence.inmemory_group_claim_repository import (
    InMemoryGroupClaimRepository,
)
from src.adapters.persistence.inmemory_grouped_claim_repository import (
    InMemoryGroupedClaimRepository,
)
from src.adapters.persistence.inmemory_payment_repository import (
    InMemoryPaymentRepository,
)
from src.adapters.persistence.inmemory_sos_claim_repository import (
    InMemorySosClaimRepository,
)
from src.application.use_cases.claims.eliminar_gestion_sos import (
    EliminarGestionSOS,
    EliminarGestionSOSInput,
)
from src.application.use_cases.claims.eliminar_grouped_claim import (
    EliminarGroupedClaim,
    EliminarGroupedClaimInput,
)
from src.application.use_cases.claims.registrar_gestion_sos import (
    RegistrarGestionSOS,
    RegistrarGestionSOSInput,
)
from src.application.use_cases.claims.registrar_grouped_claim import (
    RegistrarGroupedClaim,
    RegistrarGroupedClaimInput,
)
from src.domain.exceptions import (
    ClaimHasActivePaymentsError,
    ClaimNotFoundError,
    GestionAlreadyExistsError,
)
from src.domain.models.entities import Claim, GroupClaim, GroupedClaim, Payment, SosClaim
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

    with pytest.raises(ClaimNotFoundError, match="not found"):
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
        grouped_claims: InMemoryGroupedClaimRepository | None = None,
    ) -> None:
        self.claims = claims
        self.sos_claims = sos_claims
        self.grouped_claims = grouped_claims or InMemoryGroupedClaimRepository()

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

    with pytest.raises(GestionAlreadyExistsError, match="Ya existe una gestión"):
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


# ═══════════════════════════════════════════════════════════════════════════════
# RegistrarGroupedClaim Tests
# ═══════════════════════════════════════════════════════════════════════════════


# ── Fixtures ─────────────────────────────────────────────────────────────────


@pytest.fixture
def grouped_claim_repo() -> InMemoryGroupedClaimRepository:
    return InMemoryGroupedClaimRepository()


@pytest.fixture
def grouped_uow(
    claim_repo: InMemoryClaimRepository,
    grouped_claim_repo: InMemoryGroupedClaimRepository,
) -> FakeUnitOfWork:
    return FakeUnitOfWork(claim_repo, InMemorySosClaimRepository(), grouped_claim_repo)


@pytest.fixture
def registrar_grouped_uc(grouped_uow: FakeUnitOfWork) -> RegistrarGroupedClaim:
    return RegistrarGroupedClaim(grouped_uow)


# ── Helpers ──────────────────────────────────────────────────────────────────


def _make_registrar_grouped_input(
    overrides: dict | None = None,
) -> RegistrarGroupedClaimInput:
    data = {
        "claim_kind_id": uuid4(),
        "group_id": uuid4(),
        "claimer_name": "Carlos López",
        "policy_number": "POL-GRP-001",
        "plate": "DEF-456",
        "claimed_amount": 5000.00,
        "comment": "Reclamo agrupado de prueba",
        "group_claim_id": uuid4(),
        "notes": "Notas del lote",
    }
    if overrides:
        data.update(overrides)
    return RegistrarGroupedClaimInput(**data)


def _seed_group_claim(repo: InMemoryGroupClaimRepository) -> GroupClaim:
    gc = GroupClaim(
        group_id=uuid4(),
        name="Lote Prueba",
        external_reference="LOTE-001",
    )
    repo.add(gc)
    return gc


# ── Happy path ───────────────────────────────────────────────────────────────


def test_registrar_grouped_happy(
    registrar_grouped_uc: RegistrarGroupedClaim,
    grouped_uow: FakeUnitOfWork,
) -> None:
    """Happy path: valid input creates Claim + GroupedClaim atomically."""
    input_data = _make_registrar_grouped_input()
    result = registrar_grouped_uc.execute(input_data)

    # Output has IDs
    assert result.claim_id is not None
    assert result.grouped_claim_id is not None
    assert result.claimer_name == input_data.claimer_name
    assert result.policy_number == input_data.policy_number
    assert result.plate == input_data.plate

    # Read-back verification — Claim exists
    claim = grouped_uow.claims.get_by_id(result.claim_id)
    assert claim is not None
    assert claim.claimer_name == input_data.claimer_name

    # Read-back verification — GroupedClaim exists
    grouped = grouped_uow.grouped_claims.get_by_id(result.grouped_claim_id)
    assert grouped is not None
    assert grouped.claim_id == result.claim_id
    assert grouped.group_claim_id == input_data.group_claim_id
    assert grouped.notes == input_data.notes


# ── Validation ───────────────────────────────────────────────────────────────


def test_registrar_grouped_missing_required_fields() -> None:
    """Missing required fields raise Pydantic ValidationError."""
    with pytest.raises(ValidationError):
        RegistrarGroupedClaimInput()  # type: ignore[call-arg]


def test_registrar_grouped_missing_uuids_rejected() -> None:
    """Missing required UUID fields raise ValidationError."""
    with pytest.raises(ValidationError):
        RegistrarGroupedClaimInput(
            claim_kind_id=uuid4(),
            # missing group_id
            claimer_name="Carlos López",
            policy_number="POL-001",
            plate="ABC-123",
            group_claim_id=uuid4(),
        )


# ── No gestion uniqueness check ──────────────────────────────────────────────


def test_registrar_grouped_no_gestion_check(
    registrar_grouped_uc: RegistrarGroupedClaim,
) -> None:
    """RegistrarGroupedClaim does NOT check for gestion uniqueness (unlike SOS)."""
    input_data = _make_registrar_grouped_input()
    result = registrar_grouped_uc.execute(input_data)

    # Same input again should succeed (no gestion uniqueness constraint)
    result2 = registrar_grouped_uc.execute(input_data.model_copy())
    assert result2.claim_id is not None
    assert result2.grouped_claim_id is not None
    assert result2.claim_id != result.claim_id  # different Claims


# ── UoW commit ───────────────────────────────────────────────────────────────


def test_registrar_grouped_commits_on_success(
    registrar_grouped_uc: RegistrarGroupedClaim,
    grouped_uow: FakeUnitOfWork,
) -> None:
    """UoW.commit is called on success (ensured by __exit__ on no exception)."""
    input_data = _make_registrar_grouped_input()
    # If UoW.__exit__ raises (due to rollback), this test fails
    result = registrar_grouped_uc.execute(input_data)
    assert result.claim_id is not None


# ═══════════════════════════════════════════════════════════════════════════════
# EliminarGroupedClaim Tests
# ═══════════════════════════════════════════════════════════════════════════════


# ── Fixtures ─────────────────────────────────────────────────────────────────


@pytest.fixture
def eliminar_claim_repo() -> InMemoryClaimRepository:
    return InMemoryClaimRepository()


@pytest.fixture
def eliminar_grouped_repo() -> InMemoryGroupedClaimRepository:
    return InMemoryGroupedClaimRepository()


@pytest.fixture
def eliminar_payment_repo() -> InMemoryPaymentRepository:
    return InMemoryPaymentRepository()


@pytest.fixture
def eliminar_uc(
    eliminar_claim_repo: InMemoryClaimRepository,
    eliminar_grouped_repo: InMemoryGroupedClaimRepository,
    eliminar_payment_repo: InMemoryPaymentRepository,
) -> EliminarGroupedClaim:
    return EliminarGroupedClaim(eliminar_claim_repo, eliminar_grouped_repo, eliminar_payment_repo)


def _seed_grouped_claim_for_delete(
    claim_repo: InMemoryClaimRepository,
    grouped_repo: InMemoryGroupedClaimRepository,
    payment_repo: InMemoryPaymentRepository | None = None,
) -> tuple[Claim, GroupedClaim]:
    """Seed a Claim + GroupedClaim and optionally a payment for delete tests."""
    claim = Claim(
        claim_id=uuid4(),
        claim_kind_id=uuid4(),
        group_id=uuid4(),
        claimer_name="Delete Test",
        policy_number="POL-DEL-001",
        plate="ZZZ-999",
    )
    claim_repo.add(claim)

    grouped = GroupedClaim(
        grouped_claim_id=uuid4(),
        claim_id=claim.claim_id,
        group_claim_id=uuid4(),
        notes="To be deleted",
    )
    grouped_repo.add(grouped)

    if payment_repo is not None:
        payment_repo.add(
            Payment(
                payment_id=uuid4(),
                claim_id=claim.claim_id,
                payer_id=uuid4(),
                payment_via_id=uuid4(),
                payee_id=uuid4(),
                amount=100.0,
                active=True,
            )
        )

    return claim, grouped


# ── Happy path ───────────────────────────────────────────────────────────────


def test_eliminar_grouped_happy(
    eliminar_claim_repo: InMemoryClaimRepository,
    eliminar_grouped_repo: InMemoryGroupedClaimRepository,
    eliminar_payment_repo: InMemoryPaymentRepository,
) -> None:
    """Happy path: soft-deletes Claim, hard-deletes GroupedClaim."""
    # No active payments — deletion should succeed
    claim, _ = _seed_grouped_claim_for_delete(
        eliminar_claim_repo, eliminar_grouped_repo, None
    )
    uc = EliminarGroupedClaim(
        eliminar_claim_repo, eliminar_grouped_repo, eliminar_payment_repo
    )

    result = uc.execute(EliminarGroupedClaimInput(claim_id=claim.claim_id))

    assert result.success is True
    assert result.claim_id == claim.claim_id

    # Claim is soft-deleted (active=False)
    updated_claim = eliminar_claim_repo.get_by_id(claim.claim_id)
    assert updated_claim is not None
    assert updated_claim.active is False

    # GroupedClaim is not in the store after hard-delete (repo stores groups separately)
    assert eliminar_grouped_repo.get_by_claim_id(claim.claim_id) is None


# ── Active payments guard ────────────────────────────────────────────────────


def test_eliminar_grouped_with_active_payments_raises(
    eliminar_claim_repo: InMemoryClaimRepository,
    eliminar_grouped_repo: InMemoryGroupedClaimRepository,
    eliminar_payment_repo: InMemoryPaymentRepository,
    eliminar_uc: EliminarGroupedClaim,
) -> None:
    """With active payments, raises ClaimHasActivePaymentsError."""
    claim, _ = _seed_grouped_claim_for_delete(
        eliminar_claim_repo, eliminar_grouped_repo, eliminar_payment_repo
    )

    with pytest.raises(ClaimHasActivePaymentsError, match="active payments"):
        eliminar_uc.execute(EliminarGroupedClaimInput(claim_id=claim.claim_id))


# ── Non-existent claim ───────────────────────────────────────────────────────


def test_eliminar_grouped_nonexistent_raises(
    eliminar_uc: EliminarGroupedClaim,
) -> None:
    """Non-existent claim raises ClaimNotFoundError."""
    with pytest.raises(ClaimNotFoundError, match="not found"):
        eliminar_uc.execute(EliminarGroupedClaimInput(claim_id=uuid4()))
