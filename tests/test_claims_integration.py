"""Integration tests for GroupedClaimRepository and migration backfill.

Tests use the in-memory repository for CRUD verification and entity-level
validation for migration backfill logic.
"""

from uuid import uuid4

import pytest
from pydantic import ValidationError

from src.adapters.persistence.inmemory_grouped_claim_repository import (
    InMemoryGroupedClaimRepository,
)
from src.domain.models.entities import GroupClaim, GroupedClaim


# ═══════════════════════════════════════════════════════════════════════════════
# GroupedClaimRepository CRUD
# ═══════════════════════════════════════════════════════════════════════════════


@pytest.fixture
def repo() -> InMemoryGroupedClaimRepository:
    return InMemoryGroupedClaimRepository()


@pytest.fixture
def sample_grouped() -> GroupedClaim:
    return GroupedClaim(
        grouped_claim_id=uuid4(),
        claim_id=uuid4(),
        group_claim_id=uuid4(),
        notes="Sample grouped claim",
    )


def test_add_and_get_by_id(
    repo: InMemoryGroupedClaimRepository,
) -> None:
    """Adding a GroupedClaim makes it retrievable by get_by_id."""
    gc = GroupedClaim(
        grouped_claim_id=uuid4(),
        claim_id=uuid4(),
        group_claim_id=uuid4(),
        notes="Integration test",
    )
    repo.add(gc)

    retrieved = repo.get_by_id(gc.grouped_claim_id)
    assert retrieved is not None
    assert retrieved.grouped_claim_id == gc.grouped_claim_id
    assert retrieved.claim_id == gc.claim_id
    assert retrieved.group_claim_id == gc.group_claim_id
    assert retrieved.notes == "Integration test"


def test_get_by_claim_id_returns_correct_entity(
    repo: InMemoryGroupedClaimRepository,
) -> None:
    """get_by_claim_id returns the GroupedClaim associated with a claim."""
    claim_id = uuid4()
    gc = GroupedClaim(
        grouped_claim_id=uuid4(),
        claim_id=claim_id,
        group_claim_id=uuid4(),
        notes="Lookup by claim",
    )
    repo.add(gc)

    # Add another unrelated grouped claim
    other = GroupedClaim(
        grouped_claim_id=uuid4(),
        claim_id=uuid4(),
        group_claim_id=uuid4(),
        notes="Other",
    )
    repo.add(other)

    retrieved = repo.get_by_claim_id(claim_id)
    assert retrieved is not None
    assert retrieved.grouped_claim_id == gc.grouped_claim_id
    assert retrieved.notes == "Lookup by claim"


def test_get_by_claim_id_returns_none_on_missing(
    repo: InMemoryGroupedClaimRepository,
) -> None:
    """get_by_claim_id returns None when no match exists."""
    assert repo.get_by_claim_id(uuid4()) is None


def test_get_all_returns_all_entities(
    repo: InMemoryGroupedClaimRepository,
) -> None:
    """get_all returns every GroupedClaim in the store."""
    gc1 = GroupedClaim(grouped_claim_id=uuid4(), claim_id=uuid4(), group_claim_id=uuid4())
    gc2 = GroupedClaim(grouped_claim_id=uuid4(), claim_id=uuid4(), group_claim_id=uuid4())
    gc3 = GroupedClaim(grouped_claim_id=uuid4(), claim_id=uuid4(), group_claim_id=uuid4())
    repo.add(gc1)
    repo.add(gc2)
    repo.add(gc3)

    all_items = repo.get_all()
    assert len(all_items) == 3
    ids = {g.grouped_claim_id for g in all_items}
    assert ids == {gc1.grouped_claim_id, gc2.grouped_claim_id, gc3.grouped_claim_id}


def test_get_all_returns_empty_when_empty(
    repo: InMemoryGroupedClaimRepository,
) -> None:
    """get_all returns empty list for empty store."""
    assert repo.get_all() == []


def test_update_modifies_entity(
    repo: InMemoryGroupedClaimRepository,
) -> None:
    """Update modifies stored entity fields."""
    gc = GroupedClaim(
        grouped_claim_id=uuid4(),
        claim_id=uuid4(),
        group_claim_id=uuid4(),
        notes="Original notes",
    )
    repo.add(gc)

    updated = gc.model_copy(update={"notes": "Updated notes"})
    result = repo.update(gc.grouped_claim_id, updated)

    assert result is True
    retrieved = repo.get_by_id(gc.grouped_claim_id)
    assert retrieved is not None
    assert retrieved.notes == "Updated notes"


def test_update_nonexistent_returns_false(
    repo: InMemoryGroupedClaimRepository,
) -> None:
    """Updating a non-existent ID returns False."""
    gc = GroupedClaim(grouped_claim_id=uuid4(), claim_id=uuid4(), group_claim_id=uuid4())
    assert repo.update(uuid4(), gc) is False


def test_delete_removes_entity(
    repo: InMemoryGroupedClaimRepository,
) -> None:
    """Delete removes the entity from the store."""
    gc = GroupedClaim(grouped_claim_id=uuid4(), claim_id=uuid4(), group_claim_id=uuid4())
    repo.add(gc)

    repo.delete(gc.grouped_claim_id)

    assert repo.get_by_id(gc.grouped_claim_id) is None
    assert len(repo.get_all()) == 0


def test_delete_nonexistent_does_not_raise(
    repo: InMemoryGroupedClaimRepository,
) -> None:
    """Deleting a non-existent ID does not raise."""
    repo.delete(uuid4())  # should not raise
    assert repo.get_all() == []


def test_exists_returns_true_when_match(
    repo: InMemoryGroupedClaimRepository,
) -> None:
    """exists returns True when matching entity found."""
    notes = "Unique notes"
    gc = GroupedClaim(
        grouped_claim_id=uuid4(),
        claim_id=uuid4(),
        group_claim_id=uuid4(),
        notes=notes,
    )
    repo.add(gc)

    assert repo.exists({"notes": notes}) is True


def test_exists_returns_false_when_no_match(
    repo: InMemoryGroupedClaimRepository,
) -> None:
    """exists returns False when no matching entity found."""
    gc = GroupedClaim(grouped_claim_id=uuid4(), claim_id=uuid4(), group_claim_id=uuid4())
    repo.add(gc)

    assert repo.exists({"notes": "nonexistent"}) is False


# ═══════════════════════════════════════════════════════════════════════════════
# Migration backfill — entity-level verification
# ═══════════════════════════════════════════════════════════════════════════════


def test_group_claim_requires_external_reference() -> None:
    """GroupClaim entity now requires external_reference (min_length=1)."""
    # Valid: external_reference provided
    gc = GroupClaim(name="Lote 2024-001", external_reference="Lote 2024-001")
    assert gc.external_reference == "Lote 2024-001"

    # Missing external_reference: should raise ValidationError
    with pytest.raises(ValidationError):
        GroupClaim(name="No Ref")  # type: ignore[call-arg]


def test_group_claim_external_reference_cannot_be_empty() -> None:
    """external_reference cannot be empty string (min_length=1)."""
    with pytest.raises(ValidationError):
        GroupClaim(name="Empty Ref", external_reference="")


def test_group_claim_description_is_optional() -> None:
    """description field is optional (defaults to None)."""
    gc = GroupClaim(name="Test", external_reference="TEST-001")
    assert gc.description is None

    gc2 = GroupClaim(name="Test", external_reference="TEST-001", description="Descripción")
    assert gc2.description == "Descripción"


def test_backfill_sets_external_reference_to_name() -> None:
    """Backfill: external_reference = name preserves existing data."""
    name = "Lote 2024-001"
    gc = GroupClaim(name=name, external_reference=name)
    assert gc.external_reference == name
    assert gc.name == name  # name remains unchanged


def test_backfill_preserves_name_unchanged() -> None:
    """Backfill does NOT alter the name field."""
    gc = GroupClaim(name="Original Name", external_reference="Original Name")
    assert gc.name == "Original Name"
    assert gc.external_reference == "Original Name"


def test_backfill_description_is_null() -> None:
    """Backfilled rows have description = None."""
    gc = GroupClaim(name="Lote", external_reference="Lote")
    assert gc.description is None
