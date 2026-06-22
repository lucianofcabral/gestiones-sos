"""Unit tests for ObtenerGestionPorId use case — fetch claim detail."""

from datetime import datetime
from uuid import UUID, uuid4

import pytest

from src.adapters.persistence.inmemory_claim_kind_repository import (
    InMemoryClaimKindRepository,
)
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
from src.application.use_cases.claims.obtener_gestion_por_id import (
    GestionDetalleDTO,
    GroupedClaimDetailDTO,
    ObtenerGestionPorId,
    ObtenerGestionPorIdInput,
    PaymentDTO,
    SosClaimDetailDTO,
)
from src.domain.exceptions import ClaimNotFoundError
from src.domain.models.entities import Claim, ClaimKind, GroupClaim, GroupedClaim, Payment, SosClaim


# ── Fixtures ─────────────────────────────────────────────────────────────────


@pytest.fixture
def claim_repo() -> InMemoryClaimRepository:
    return InMemoryClaimRepository()


@pytest.fixture
def sos_claim_repo() -> InMemorySosClaimRepository:
    return InMemorySosClaimRepository()


@pytest.fixture
def group_claim_repo(
    claim_repo: InMemoryClaimRepository,
) -> InMemoryGroupClaimRepository:
    return InMemoryGroupClaimRepository(claim_store=claim_repo._store)


@pytest.fixture
def claim_kind_repo() -> InMemoryClaimKindRepository:
    return InMemoryClaimKindRepository()


@pytest.fixture
def payment_repo() -> InMemoryPaymentRepository:
    return InMemoryPaymentRepository()


@pytest.fixture
def grouped_claim_repo() -> InMemoryGroupedClaimRepository:
    return InMemoryGroupedClaimRepository()


@pytest.fixture
def use_case(
    claim_repo: InMemoryClaimRepository,
    sos_claim_repo: InMemorySosClaimRepository,
    group_claim_repo: InMemoryGroupClaimRepository,
    claim_kind_repo: InMemoryClaimKindRepository,
    payment_repo: InMemoryPaymentRepository,
    grouped_claim_repo: InMemoryGroupedClaimRepository,
) -> ObtenerGestionPorId:
    return ObtenerGestionPorId(
        claim_repo=claim_repo,
        sos_claim_repo=sos_claim_repo,
        group_claim_repo=group_claim_repo,
        claim_kind_repo=claim_kind_repo,
        payment_repo=payment_repo,
        grouped_claim_repo=grouped_claim_repo,
    )


# ── Helpers ──────────────────────────────────────────────────────────────────


def _seed_claim(
    repo: InMemoryClaimRepository,
    overrides: dict | None = None,
) -> Claim:
    data = {
        "claim_id": uuid4(),
        "claim_kind_id": uuid4(),
        "group_id": uuid4(),
        "claimer_name": "Juan Pérez",
        "policy_number": "POL-001",
        "plate": "ABC-123",
        "claimed_amount": 1500.00,
        "comment": "Comentario de prueba",
        "solved": False,
        "active": True,
        "created_at": datetime(2025, 6, 1, 10, 0, 0),
    }
    if overrides:
        data.update(overrides)
    claim = Claim(**data)
    repo.add(claim)
    return claim


def _seed_sos_claim(
    repo: InMemorySosClaimRepository,
    claim_id: UUID,
    overrides: dict | None = None,
) -> SosClaim:
    data = {
        "sos_claim_id": uuid4(),
        "claim_id": claim_id,
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
    sc = SosClaim(**data)
    repo.add(sc)
    return sc


def _seed_group(
    repo: InMemoryGroupClaimRepository,
    overrides: dict | None = None,
) -> GroupClaim:
    data = {
        "group_id": uuid4(),
        "name": "Grupo Prueba",
        "external_reference": "LOTE-001",
    }
    if overrides:
        data.update(overrides)
    group = GroupClaim(**data)
    repo.add(group)
    return group


def _seed_claim_kind(
    repo: InMemoryClaimKindRepository,
    overrides: dict | None = None,
) -> ClaimKind:
    data = {
        "claim_kind_id": uuid4(),
        "name": "Tipo Prueba",
        "active": True,
    }
    if overrides:
        data.update(overrides)
    kind = ClaimKind(**data)
    repo.add(kind)
    return kind


def _seed_payment(
    repo: InMemoryPaymentRepository,
    claim_id: UUID,
    overrides: dict | None = None,
) -> Payment:
    data = {
        "payment_id": uuid4(),
        "claim_id": claim_id,
        "payer_id": uuid4(),
        "payment_via_id": uuid4(),
        "payee_id": uuid4(),
        "amount": 500.00,
        "active": True,
        "created_date": datetime(2025, 6, 15, 14, 0, 0),
    }
    if overrides:
        data.update(overrides)
    p = Payment(**data)
    repo.add(p)
    return p


# ── Happy path ───────────────────────────────────────────────────────────────


def test_happy_path_returns_full_detail(
    use_case: ObtenerGestionPorId,
    claim_repo: InMemoryClaimRepository,
    sos_claim_repo: InMemorySosClaimRepository,
    group_claim_repo: InMemoryGroupClaimRepository,
    claim_kind_repo: InMemoryClaimKindRepository,
    payment_repo: InMemoryPaymentRepository,
) -> None:
    """Happy path: claim with SosClaims, group, kind, and payments."""
    kind = _seed_claim_kind(claim_kind_repo)
    claim = _seed_claim(claim_repo, overrides={"claim_kind_id": kind.claim_kind_id})
    _seed_group(group_claim_repo, overrides={"group_id": claim.group_id})
    _seed_sos_claim(sos_claim_repo, claim.claim_id, overrides={"gestion": 1001})
    _seed_sos_claim(sos_claim_repo, claim.claim_id, overrides={"gestion": 1002})
    _seed_payment(payment_repo, claim.claim_id, overrides={"amount": 500.00})
    _seed_payment(payment_repo, claim.claim_id, overrides={"amount": 750.00})

    result = use_case.execute(ObtenerGestionPorIdInput(claim_id=claim.claim_id))

    assert isinstance(result, GestionDetalleDTO)
    assert result.claim_id == claim.claim_id
    assert result.claimer_name == "Juan Pérez"
    assert result.policy_number == "POL-001"
    assert result.plate == "ABC-123"
    assert result.claimed_amount == 1500.00
    assert result.comment == "Comentario de prueba"
    assert result.solved is False
    assert result.active is True
    assert result.group_name == "Grupo Prueba"
    assert result.claim_kind_name == "Tipo Prueba"
    assert len(result.sos_records) == 2
    assert len(result.payments) == 2

    # Verify SOS records
    gestions = {sc.gestion for sc in result.sos_records}
    assert gestions == {1001, 1002}

    # Verify payments
    amounts = {p.amount for p in result.payments}
    assert amounts == {500.00, 750.00}


# ── Claim not found ──────────────────────────────────────────────────────────


def test_claim_not_found_raises_error(
    use_case: ObtenerGestionPorId,
) -> None:
    """Non-existent claim_id raises ClaimNotFoundError."""
    with pytest.raises(ClaimNotFoundError):
        use_case.execute(ObtenerGestionPorIdInput(claim_id=uuid4()))


# ── No SosClaim records ──────────────────────────────────────────────────────


def test_claim_without_sos_claims_returns_empty_list(
    use_case: ObtenerGestionPorId,
    claim_repo: InMemoryClaimRepository,
    group_claim_repo: InMemoryGroupClaimRepository,
    claim_kind_repo: InMemoryClaimKindRepository,
    payment_repo: InMemoryPaymentRepository,
) -> None:
    """Claim with no SosClaim records returns empty sos_records list."""
    kind = _seed_claim_kind(claim_kind_repo)
    claim = _seed_claim(claim_repo, overrides={"claim_kind_id": kind.claim_kind_id})
    _seed_group(group_claim_repo, overrides={"group_id": claim.group_id})
    _seed_payment(payment_repo, claim.claim_id)

    result = use_case.execute(ObtenerGestionPorIdInput(claim_id=claim.claim_id))

    assert result.sos_records == []
    assert result.claimer_name == claim.claimer_name
    assert len(result.payments) == 1


# ── No payments ──────────────────────────────────────────────────────────────


def test_claim_without_payments_returns_empty_list(
    use_case: ObtenerGestionPorId,
    claim_repo: InMemoryClaimRepository,
    sos_claim_repo: InMemorySosClaimRepository,
    group_claim_repo: InMemoryGroupClaimRepository,
    claim_kind_repo: InMemoryClaimKindRepository,
) -> None:
    """Claim with no payments returns empty payments list."""
    kind = _seed_claim_kind(claim_kind_repo)
    claim = _seed_claim(claim_repo, overrides={"claim_kind_id": kind.claim_kind_id})
    _seed_group(group_claim_repo, overrides={"group_id": claim.group_id})
    _seed_sos_claim(sos_claim_repo, claim.claim_id)

    result = use_case.execute(ObtenerGestionPorIdInput(claim_id=claim.claim_id))

    assert result.payments == []
    assert len(result.sos_records) == 1


# ── Missing group/kind (None guard) ──────────────────────────────────────────


def test_missing_group_and_kind_return_empty_strings(
    use_case: ObtenerGestionPorId,
    claim_repo: InMemoryClaimRepository,
    sos_claim_repo: InMemorySosClaimRepository,
    payment_repo: InMemoryPaymentRepository,
) -> None:
    """Missing group claim or kind returns empty strings for their names."""
    claim = _seed_claim(claim_repo)  # group and kind ids don't match anything
    _seed_sos_claim(sos_claim_repo, claim.claim_id)
    _seed_payment(payment_repo, claim.claim_id)

    result = use_case.execute(ObtenerGestionPorIdInput(claim_id=claim.claim_id))

    assert result.group_name == ""
    assert result.claim_kind_name == ""
    assert len(result.sos_records) == 1
    assert len(result.payments) == 1


# ── DTO type checks ──────────────────────────────────────────────────────────


def test_dto_types_are_correct(
    use_case: ObtenerGestionPorId,
    claim_repo: InMemoryClaimRepository,
    sos_claim_repo: InMemorySosClaimRepository,
    group_claim_repo: InMemoryGroupClaimRepository,
    claim_kind_repo: InMemoryClaimKindRepository,
    payment_repo: InMemoryPaymentRepository,
) -> None:
    """All nested DTOs have correct types."""
    kind = _seed_claim_kind(claim_kind_repo)
    claim = _seed_claim(claim_repo, overrides={"claim_kind_id": kind.claim_kind_id})
    _seed_group(group_claim_repo, overrides={"group_id": claim.group_id})
    _seed_sos_claim(sos_claim_repo, claim.claim_id)
    _seed_payment(payment_repo, claim.claim_id)

    result = use_case.execute(ObtenerGestionPorIdInput(claim_id=claim.claim_id))

    for sc in result.sos_records:
        assert isinstance(sc, SosClaimDetailDTO)
        assert isinstance(sc.sos_claim_id, UUID)
        assert isinstance(sc.gestion, int)
        assert isinstance(sc.itr, int)

    for p in result.payments:
        assert isinstance(p, PaymentDTO)
        assert isinstance(p.payment_id, UUID)
        assert isinstance(p.amount, float)
        assert isinstance(p.created_date, datetime)
        assert isinstance(p.active, bool)


# ═══════════════════════════════════════════════════════════════════════════════
# Grouped claim type dispatch
# ═══════════════════════════════════════════════════════════════════════════════


def _seed_grouped_claim_detail(
    claim_repo: InMemoryClaimRepository,
    grouped_claim_repo: InMemoryGroupedClaimRepository,
    group_claim_repo: InMemoryGroupClaimRepository,
    claim_kind_repo: InMemoryClaimKindRepository,
    payment_repo: InMemoryPaymentRepository,
    group_id: UUID | None = None,
    overrides: dict | None = None,
) -> tuple[ObtenerGestionPorId, Claim]:
    """Seed a full Grouped claim scenario, return (use_case, claim)."""
    kind = _seed_claim_kind(claim_kind_repo, overrides={"name": "Grouped"})

    batch_group_id = group_id or uuid4()
    batch = GroupClaim(
        group_id=batch_group_id,
        name="Lote Prueba",
        external_reference="LOTE-2024-001",
        description="Lote de prueba para testing",
    )
    group_claim_repo.add(batch)

    claim_data = {
        "claim_id": uuid4(),
        "claim_kind_id": kind.claim_kind_id,
        "group_id": batch_group_id,  # must match batch group_id for name lookup
        "claimer_name": "Grupo Test",
        "policy_number": "POL-GRP-001",
        "plate": "GRP-123",
        "claimed_amount": 3000.00,
        "comment": "Comentario grupo",
        "solved": False,
        "active": True,
        "created_at": datetime(2025, 7, 1, 9, 0, 0),
    }
    if overrides:
        claim_data.update(overrides)
    claim = Claim(**claim_data)
    claim_repo.add(claim)

    grouped_claim = GroupedClaim(
        grouped_claim_id=uuid4(),
        claim_id=claim.claim_id,
        group_claim_id=batch.group_id,
        notes="Notas del lote agrupado",
        created_at=datetime(2025, 7, 1, 9, 30, 0),
    )
    grouped_claim_repo.add(grouped_claim)

    payment = Payment(
        payment_id=uuid4(),
        claim_id=claim.claim_id,
        payer_id=uuid4(),
        payment_via_id=uuid4(),
        payee_id=uuid4(),
        amount=750.00,
        active=True,
        created_date=datetime(2025, 7, 2, 14, 0, 0),
    )
    payment_repo.add(payment)

    uc = ObtenerGestionPorId(
        claim_repo=claim_repo,
        sos_claim_repo=InMemorySosClaimRepository(),
        group_claim_repo=group_claim_repo,
        claim_kind_repo=claim_kind_repo,
        payment_repo=payment_repo,
        grouped_claim_repo=grouped_claim_repo,
    )
    return uc, claim


def test_grouped_claim_returns_grouped_data(
    claim_repo: InMemoryClaimRepository,
    grouped_claim_repo: InMemoryGroupedClaimRepository,
    group_claim_repo: InMemoryGroupClaimRepository,
    claim_kind_repo: InMemoryClaimKindRepository,
    payment_repo: InMemoryPaymentRepository,
) -> None:
    """Grouped claim: grouped_data populated, sos_records empty."""
    uc, claim = _seed_grouped_claim_detail(
        claim_repo, grouped_claim_repo, group_claim_repo,
        claim_kind_repo, payment_repo,
    )

    result = uc.execute(ObtenerGestionPorIdInput(claim_id=claim.claim_id))

    # Type-specific data
    assert result.grouped_data is not None
    assert result.grouped_data.external_reference == "LOTE-2024-001"
    assert result.grouped_data.notes == "Notas del lote agrupado"
    assert isinstance(result.grouped_data.created_at, datetime)
    assert isinstance(result.grouped_data.group_claim_id, UUID)

    # SOS path: should be empty
    assert result.sos_records == []

    # Common data intact
    assert result.claim_id == claim.claim_id
    assert result.claimer_name == "Grupo Test"
    assert result.policy_number == "POL-GRP-001"
    assert result.plate == "GRP-123"
    assert result.claimed_amount == 3000.00
    assert result.comment == "Comentario grupo"
    assert result.group_name == "Lote Prueba"
    assert result.claim_kind_name == "Grouped"
    assert len(result.payments) == 1


def test_sos_claim_grouped_data_is_none(
    use_case: ObtenerGestionPorId,
    claim_repo: InMemoryClaimRepository,
    sos_claim_repo: InMemorySosClaimRepository,
    group_claim_repo: InMemoryGroupClaimRepository,
    claim_kind_repo: InMemoryClaimKindRepository,
    payment_repo: InMemoryPaymentRepository,
) -> None:
    """SOS claim: grouped_data is None, sos_records populated."""
    kind = _seed_claim_kind(claim_kind_repo, overrides={"name": "SOS"})
    claim = _seed_claim(claim_repo, overrides={"claim_kind_id": kind.claim_kind_id})
    _seed_group(group_claim_repo, overrides={"group_id": claim.group_id})
    _seed_sos_claim(sos_claim_repo, claim.claim_id, overrides={"gestion": 1001})

    result = use_case.execute(ObtenerGestionPorIdInput(claim_id=claim.claim_id))

    assert result.grouped_data is None
    assert len(result.sos_records) == 1
    assert result.sos_records[0].gestion == 1001


def test_grouped_claim_detail_dto_fields(
    claim_repo: InMemoryClaimRepository,
    grouped_claim_repo: InMemoryGroupedClaimRepository,
    group_claim_repo: InMemoryGroupClaimRepository,
    claim_kind_repo: InMemoryClaimKindRepository,
    payment_repo: InMemoryPaymentRepository,
) -> None:
    """GroupedClaimDetailDTO has all required fields."""
    uc, claim = _seed_grouped_claim_detail(
        claim_repo, grouped_claim_repo, group_claim_repo,
        claim_kind_repo, payment_repo,
    )
    result = uc.execute(ObtenerGestionPorIdInput(claim_id=claim.claim_id))

    assert result.grouped_data is not None
    gdto = result.grouped_data
    assert isinstance(gdto, GroupedClaimDetailDTO)
    assert isinstance(gdto.group_claim_id, UUID)
    assert isinstance(gdto.external_reference, str)
    assert gdto.external_reference == "LOTE-2024-001"
    assert isinstance(gdto.notes, str)
    assert gdto.notes == "Notas del lote agrupado"
    assert isinstance(gdto.created_at, datetime)
