"""UI dispatch tests — kind classification, submit dispatch, delete dispatch.

These test the pure-logic portions of the UI pages without a browser/headless
rendering engine. Focus on dispatch decisions: given a claim kind name or ID,
which use case is called?
"""

from uuid import uuid4

from src.application.use_cases.claims.eliminar_gestion_sos import (
    EliminarGestionSOSInput,
)
from src.application.use_cases.claims.eliminar_grouped_claim import (
    EliminarGroupedClaimInput,
)
from src.application.use_cases.claims.registrar_gestion_sos import (
    RegistrarGestionSOSInput,
)
from src.application.use_cases.claims.registrar_grouped_claim import (
    RegistrarGroupedClaimInput,
)
from src.domain.models.entities import ClaimKind


# ═══════════════════════════════════════════════════════════════════════════════
# Kind classification helpers (mirrors logic from gestiones_nueva.py)
# ═══════════════════════════════════════════════════════════════════════════════


def _sos_kind_ids(claim_kinds: list[ClaimKind]) -> set[str]:
    return {str(k.claim_kind_id) for k in claim_kinds if k.name.upper() == "SOS"}


def _grouped_kind_ids(claim_kinds: list[ClaimKind]) -> set[str]:
    return {str(k.claim_kind_id) for k in claim_kinds if k.name.upper() == "GROUPED"}


# ── Tests ────────────────────────────────────────────────────────────────────


def test_sos_kind_classification() -> None:
    """SOS kind IDs are correctly identified from claim_kinds list."""
    sos_id = uuid4()
    kinds = [
        ClaimKind(claim_kind_id=sos_id, name="SOS"),
        ClaimKind(claim_kind_id=uuid4(), name="Grouped"),
        ClaimKind(claim_kind_id=uuid4(), name="Tres Arroyos"),
        ClaimKind(claim_kind_id=uuid4(), name="Ad-Hoc"),
    ]

    result = _sos_kind_ids(kinds)
    assert str(sos_id) in result
    assert len(result) == 1


def test_grouped_kind_classification() -> None:
    """Grouped kind IDs are correctly identified from claim_kinds list."""
    grouped_id = uuid4()
    kinds = [
        ClaimKind(claim_kind_id=uuid4(), name="SOS"),
        ClaimKind(claim_kind_id=grouped_id, name="Grouped"),
        ClaimKind(claim_kind_id=uuid4(), name="Tres Arroyos"),
    ]

    result = _grouped_kind_ids(kinds)
    assert str(grouped_id) in result
    assert len(result) == 1


def test_kind_classification_case_insensitive() -> None:
    """Kind name matching is case-insensitive."""
    sos_id = uuid4()
    kinds = [
        ClaimKind(claim_kind_id=sos_id, name="sos"),  # lowercase
        ClaimKind(claim_kind_id=uuid4(), name="GROUPED"),  # uppercase
    ]

    assert str(sos_id) in _sos_kind_ids(kinds)
    assert len(_sos_kind_ids(kinds)) == 1


def test_empty_kinds_returns_empty_ids() -> None:
    """Empty claim_kinds list returns empty sets."""
    assert _sos_kind_ids([]) == set()
    assert _grouped_kind_ids([]) == set()


def test_unknown_kind_not_classified() -> None:
    """Unknown kind name does not appear in SOS or Grouped sets."""
    unknown_id = uuid4()
    kinds = [ClaimKind(claim_kind_id=unknown_id, name="UnknownType")]

    assert str(unknown_id) not in _sos_kind_ids(kinds)
    assert str(unknown_id) not in _grouped_kind_ids(kinds)


# ═══════════════════════════════════════════════════════════════════════════════
# Conditional form logic — kind dispatch decision
# ═══════════════════════════════════════════════════════════════════════════════


def test_sos_kind_triggers_sos_path() -> None:
    """A kind_id in SOS set triggers the SOS form path."""
    sos_id = uuid4()
    grouped_id = uuid4()
    kinds = [
        ClaimKind(claim_kind_id=sos_id, name="SOS"),
        ClaimKind(claim_kind_id=grouped_id, name="Grouped"),
    ]
    sos_ids = _sos_kind_ids(kinds)
    grouped_ids = _grouped_kind_ids(kinds)

    assert str(sos_id) in sos_ids
    assert str(sos_id) not in grouped_ids


def test_grouped_kind_triggers_grouped_path() -> None:
    """A kind_id in Grouped set triggers the Grouped form path."""
    sos_id = uuid4()
    grouped_id = uuid4()
    kinds = [
        ClaimKind(claim_kind_id=sos_id, name="SOS"),
        ClaimKind(claim_kind_id=grouped_id, name="Grouped"),
    ]
    sos_ids = _sos_kind_ids(kinds)
    grouped_ids = _grouped_kind_ids(kinds)

    assert str(grouped_id) in grouped_ids
    assert str(grouped_id) not in sos_ids


# ═══════════════════════════════════════════════════════════════════════════════
# Submit dispatch — input type construction
# ═══════════════════════════════════════════════════════════════════════════════


def _dispatch_submit(
    kind_id: str,
    sos_kind_ids: set[str],
    grouped_kind_ids: set[str],
    shared_data: dict,
    sos_data: dict | None = None,
    grouped_data: dict | None = None,
) -> type | None:
    """Simulate the submit dispatch logic from gestiones_nueva.py.

    Returns the Input DTO class that would be constructed, or None if no match.
    """
    if kind_id in sos_kind_ids and sos_data is not None:
        return RegistrarGestionSOSInput
    elif kind_id in grouped_kind_ids and grouped_data is not None:
        return RegistrarGroupedClaimInput
    return None


def test_submit_dispatch_sos() -> None:
    """SOS kind_id constructs RegistrarGestionSOSInput."""
    sos_id = str(uuid4())
    result = _dispatch_submit(
        kind_id=sos_id,
        sos_kind_ids={sos_id},
        grouped_kind_ids=set(),
        shared_data={},
        sos_data={"gestion": 1001},
    )
    assert result is RegistrarGestionSOSInput


def test_submit_dispatch_grouped() -> None:
    """Grouped kind_id constructs RegistrarGroupedClaimInput."""
    grouped_id = str(uuid4())
    result = _dispatch_submit(
        kind_id=grouped_id,
        sos_kind_ids=set(),
        grouped_kind_ids={grouped_id},
        shared_data={},
        grouped_data={"group_claim_id": uuid4()},
    )
    assert result is RegistrarGroupedClaimInput


def test_submit_dispatch_unknown_returns_none() -> None:
    """Unknown kind_id returns None (no form path)."""
    result = _dispatch_submit(
        kind_id=str(uuid4()),
        sos_kind_ids=set(),
        grouped_kind_ids=set(),
        shared_data={},
    )
    assert result is None


# ═══════════════════════════════════════════════════════════════════════════════
# Delete dispatch — use case selection
# ═══════════════════════════════════════════════════════════════════════════════


def _dispatch_delete(
    claim_kind_name: str,
) -> type:
    """Simulate the delete dispatch logic from gestiones.py _delete_gestion.

    Returns the Input DTO class that would be used.
    """
    if claim_kind_name.upper() == "SOS":
        return EliminarGestionSOSInput
    else:
        return EliminarGroupedClaimInput


def test_delete_dispatch_sos() -> None:
    """SOS claim_kind_name dispatches to EliminarGestionSOSInput."""
    result = _dispatch_delete("SOS")
    assert result is EliminarGestionSOSInput


def test_delete_dispatch_grouped() -> None:
    """Grouped claim_kind_name dispatches to EliminarGroupedClaimInput."""
    result = _dispatch_delete("Grouped")
    assert result is EliminarGroupedClaimInput


def test_delete_dispatch_case_insensitive_sos() -> None:
    """SOS dispatch is case-insensitive."""
    assert _dispatch_delete("sos") is EliminarGestionSOSInput
    assert _dispatch_delete("Sos") is EliminarGestionSOSInput


def test_delete_dispatch_grouped_case_insensitive() -> None:
    """Grouped dispatch is case-insensitive."""
    assert _dispatch_delete("grouped") is EliminarGroupedClaimInput
    assert _dispatch_delete("GROUPED") is EliminarGroupedClaimInput


def test_delete_dispatch_unknown_kind_falls_back_to_grouped() -> None:
    """Unknown claim_kind_name falls back to EliminarGroupedClaimInput."""
    result = _dispatch_delete("UnknownType")
    assert result is EliminarGroupedClaimInput
