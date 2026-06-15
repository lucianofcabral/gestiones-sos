"""Unit tests for ObtenerGestiones use case — list claims with type dispatch."""

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
from src.adapters.persistence.inmemory_sos_claim_repository import (
    InMemorySosClaimRepository,
)
from src.application.use_cases.claims.obtener_gestiones import (
    ObtenerGestiones,
    ObtenerGestionesInput,
    ObtenerGestionesOutput,
)
from src.domain.models.entities import Claim, ClaimKind, GroupClaim, GroupedClaim, SosClaim


# ── Fixtures ─────────────────────────────────────────────────────────────────


@pytest.fixture
def claim_repo() -> InMemoryClaimRepository:
    return InMemoryClaimRepository()


@pytest.fixture
def sos_claim_repo() -> InMemorySosClaimRepository:
    return InMemorySosClaimRepository()


@pytest.fixture
def grouped_claim_repo() -> InMemoryGroupedClaimRepository:
    return InMemoryGroupedClaimRepository()


@pytest.fixture
def group_claim_repo() -> InMemoryGroupClaimRepository:
    return InMemoryGroupClaimRepository()


@pytest.fixture
def claim_kind_repo() -> InMemoryClaimKindRepository:
    return InMemoryClaimKindRepository()


@pytest.fixture
def use_case(
    claim_repo: InMemoryClaimRepository,
    sos_claim_repo: InMemorySosClaimRepository,
    grouped_claim_repo: InMemoryGroupedClaimRepository,
    group_claim_repo: InMemoryGroupClaimRepository,
    claim_kind_repo: InMemoryClaimKindRepository,
) -> ObtenerGestiones:
    return ObtenerGestiones(
        claim_repo=claim_repo,
        sos_claim_repo=sos_claim_repo,
        grouped_claim_repo=grouped_claim_repo,
        group_claim_repo=group_claim_repo,
        claim_kind_repo=claim_kind_repo,
    )


# ── Helpers ──────────────────────────────────────────────────────────────────


def _seed_claim(
    repo: InMemoryClaimRepository,
    active: bool = True,
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
        "solved": False,
        "active": active,
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
    sos = SosClaim(**data)
    repo.add(sos)
    return sos


def _seed_grouped_claim(
    repo: InMemoryGroupedClaimRepository,
    claim_id: UUID,
    group_claim_id: UUID,
    overrides: dict | None = None,
) -> GroupedClaim:
    data = {
        "grouped_claim_id": uuid4(),
        "claim_id": claim_id,
        "group_claim_id": group_claim_id,
        "notes": "Nota del lote",
    }
    if overrides:
        data.update(overrides)
    gc = GroupedClaim(**data)
    repo.add(gc)
    return gc


def _seed_group_claim(
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
    g = GroupClaim(**data)
    repo.add(g)
    return g


def _seed_claim_kind(
    repo: InMemoryClaimKindRepository,
    overrides: dict | None = None,
) -> ClaimKind:
    data = {
        "claim_kind_id": uuid4(),
        "name": "SOS",
        "active": True,
    }
    if overrides:
        data.update(overrides)
    kind = ClaimKind(**data)
    repo.add(kind)
    return kind


# ── Active-only filtering ────────────────────────────────────────────────────


def test_default_returns_only_active_claims(
    use_case: ObtenerGestiones,
    claim_repo: InMemoryClaimRepository,
    sos_claim_repo: InMemorySosClaimRepository,
) -> None:
    """Default execute() returns only active claims."""
    active_claim = _seed_claim(claim_repo, active=True)
    inactive_claim = _seed_claim(claim_repo, active=False)
    _seed_sos_claim(sos_claim_repo, active_claim.claim_id)
    _seed_sos_claim(sos_claim_repo, inactive_claim.claim_id)

    result = use_case.execute(ObtenerGestionesInput())

    assert len(result.gestiones) == 1
    assert result.gestiones[0].claim_id == active_claim.claim_id
    assert result.gestiones[0].active is True


def test_include_inactive_returns_all(
    use_case: ObtenerGestiones,
    claim_repo: InMemoryClaimRepository,
    sos_claim_repo: InMemorySosClaimRepository,
) -> None:
    """include_inactive=True returns both active and inactive claims."""
    _seed_claim(claim_repo, active=True)
    _seed_claim(claim_repo, active=False)

    result = use_case.execute(ObtenerGestionesInput(include_inactive=True))

    assert len(result.gestiones) == 2


# ── Empty state ──────────────────────────────────────────────────────────────


def test_empty_repos_return_empty_list(
    use_case: ObtenerGestiones,
) -> None:
    """Empty repos return an empty list."""
    result = use_case.execute(ObtenerGestionesInput())
    assert result.gestiones == []


def test_empty_result_with_include_inactive(
    use_case: ObtenerGestiones,
) -> None:
    """Empty repos return [] even with include_inactive=True."""
    result = use_case.execute(ObtenerGestionesInput(include_inactive=True))
    assert result.gestiones == []


# ── No data for a claim ──────────────────────────────────────────────────────


def test_claim_without_type_data_uses_empty_reference(
    use_case: ObtenerGestiones,
    claim_repo: InMemoryClaimRepository,
) -> None:
    """A claim without matching SOS or Grouped data gets an empty reference."""
    claim = _seed_claim(claim_repo, active=True)

    result = use_case.execute(ObtenerGestionesInput())

    assert len(result.gestiones) == 1
    dto = result.gestiones[0]
    assert dto.claim_id == claim.claim_id
    assert dto.gestion_or_reference == ""
    assert dto.claim_kind_name == ""


# ── DTO field mapping — SOS claim ────────────────────────────────────────────


def test_dto_field_mapping_for_sos_claim(
    use_case: ObtenerGestiones,
    claim_repo: InMemoryClaimRepository,
    sos_claim_repo: InMemorySosClaimRepository,
    claim_kind_repo: InMemoryClaimKindRepository,
) -> None:
    """SOS claims map gestion to gestion_or_reference and include kind name."""
    kind = _seed_claim_kind(claim_kind_repo, overrides={"name": "SOS"})
    fixed_claim_id = uuid4()
    _seed_claim(
        claim_repo,
        active=True,
        overrides={
            "claim_id": fixed_claim_id,
            "claim_kind_id": kind.claim_kind_id,
            "claimer_name": "María García",
            "policy_number": "POL-99999",
            "plate": "XYZ-789",
            "claimed_amount": 2500.50,
            "solved": True,
            "active": True,
        },
    )
    _seed_sos_claim(
        sos_claim_repo,
        claim_id=fixed_claim_id,
        overrides={"gestion": 2001},
    )

    result = use_case.execute(ObtenerGestionesInput())

    assert len(result.gestiones) == 1
    dto = result.gestiones[0]

    assert dto.claim_id == fixed_claim_id
    assert dto.gestion_or_reference == "2001"
    assert dto.claimer_name == "María García"
    assert dto.policy_number == "POL-99999"
    assert dto.plate == "XYZ-789"
    assert dto.claimed_amount == 2500.50
    assert dto.claim_kind_name == "SOS"
    assert dto.solved is True
    assert dto.active is True
    assert isinstance(dto.created_at, datetime)


# ── DTO field mapping — Grouped claim ────────────────────────────────────────


def test_dto_field_mapping_for_grouped_claim(
    use_case: ObtenerGestiones,
    claim_repo: InMemoryClaimRepository,
    grouped_claim_repo: InMemoryGroupedClaimRepository,
    group_claim_repo: InMemoryGroupClaimRepository,
    claim_kind_repo: InMemoryClaimKindRepository,
) -> None:
    """Grouped claims show external_reference as gestion_or_reference."""
    kind = _seed_claim_kind(claim_kind_repo, overrides={"name": "Grouped"})
    batch = _seed_group_claim(group_claim_repo, overrides={"external_reference": "LOTE-2024-001"})
    claim = _seed_claim(
        claim_repo,
        active=True,
        overrides={"claim_kind_id": kind.claim_kind_id},
    )
    _seed_grouped_claim(grouped_claim_repo, claim.claim_id, batch.group_id)

    result = use_case.execute(ObtenerGestionesInput())

    assert len(result.gestiones) == 1
    dto = result.gestiones[0]
    assert dto.gestion_or_reference == "LOTE-2024-001"
    assert dto.claim_kind_name == "Grouped"
    assert dto.claim_id == claim.claim_id


# ── Mixed types ──────────────────────────────────────────────────────────────


def test_mixed_list_shows_both_types_correctly(
    use_case: ObtenerGestiones,
    claim_repo: InMemoryClaimRepository,
    sos_claim_repo: InMemorySosClaimRepository,
    grouped_claim_repo: InMemoryGroupedClaimRepository,
    group_claim_repo: InMemoryGroupClaimRepository,
    claim_kind_repo: InMemoryClaimKindRepository,
) -> None:
    """SOS and Grouped claims both appear with correct references."""
    sos_kind = _seed_claim_kind(claim_kind_repo, overrides={"name": "SOS"})
    grouped_kind = _seed_claim_kind(claim_kind_repo, overrides={"name": "Grouped"})

    # SOS claim
    sos_claim = _seed_claim(
        claim_repo,
        active=True,
        overrides={
            "claim_kind_id": sos_kind.claim_kind_id,
            "claimer_name": "SOS User",
        },
    )
    _seed_sos_claim(sos_claim_repo, sos_claim.claim_id, overrides={"gestion": 5001})

    # Grouped claim
    batch = _seed_group_claim(group_claim_repo, overrides={"external_reference": "BATCH-001"})
    grouped_claim = _seed_claim(
        claim_repo,
        active=True,
        overrides={
            "claim_kind_id": grouped_kind.claim_kind_id,
            "claimer_name": "Grouped User",
        },
    )
    _seed_grouped_claim(grouped_claim_repo, grouped_claim.claim_id, batch.group_id)

    result = use_case.execute(ObtenerGestionesInput())

    assert len(result.gestiones) == 2

    sos_dto = next(d for d in result.gestiones if d.claimer_name == "SOS User")
    assert sos_dto.gestion_or_reference == "5001"
    assert sos_dto.claim_kind_name == "SOS"

    grouped_dto = next(d for d in result.gestiones if d.claimer_name == "Grouped User")
    assert grouped_dto.gestion_or_reference == "BATCH-001"
    assert grouped_dto.claim_kind_name == "Grouped"


# ── Output type ──────────────────────────────────────────────────────────────


def test_output_is_obtener_gestiones_output(
    use_case: ObtenerGestiones,
) -> None:
    """execute returns an ObtenerGestionesOutput instance."""
    result = use_case.execute(ObtenerGestionesInput())
    assert isinstance(result, ObtenerGestionesOutput)
    assert hasattr(result, "gestiones")
