"""Unit tests for in-memory repository implementations."""

from datetime import datetime, timedelta
from uuid import UUID, uuid4

import pytest

from src.adapters.persistence.inmemory_ncpayment_repository import (
    InMemoryNcPaymentRepository,
)
from src.adapters.persistence.inmemory_payment_repository import (
    InMemoryPaymentRepository,
)
from src.domain.models.entities import CreditNote, Payment


# ── Fixtures ─────────────────────────────────────────────────────────────────


@pytest.fixture
def repo() -> InMemoryPaymentRepository:
    return InMemoryPaymentRepository()


# ── Helpers ──────────────────────────────────────────────────────────────────


def _payment(**overrides: object) -> Payment:
    defaults: dict[str, object] = {
        "payment_id": uuid4(),
        "claim_id": uuid4(),
        "payer_id": uuid4(),
        "payee_id": uuid4(),
        "payment_via_id": uuid4(),
        "amount": 1000.0,
        "active": True,
        "created_date": datetime.now(),
    }
    merged = {**defaults, **overrides}
    return Payment(**merged)


def _seed(repo: InMemoryPaymentRepository, n: int = 3) -> list[Payment]:
    payments = [_payment() for _ in range(n)]
    for p in payments:
        repo.add(p)
    return payments


# ── BaseRepo: add / get_by_id / get_all ──────────────────────────────────────


def test_add_and_get_by_id(repo: InMemoryPaymentRepository) -> None:
    """add() stores a payment; get_by_id() retrieves it."""
    payment = _payment()
    repo.add(payment)

    result = repo.get_by_id(payment.payment_id)

    assert result is not None
    assert result.payment_id == payment.payment_id
    assert result.amount == 1000.0
    assert result.active is True


def test_get_by_id_not_found(repo: InMemoryPaymentRepository) -> None:
    """get_by_id returns None for unknown id."""
    result = repo.get_by_id(uuid4())
    assert result is None


def test_get_all_returns_all(repo: InMemoryPaymentRepository) -> None:
    """get_all returns every stored payment."""
    seeded = _seed(repo, n=3)
    result = repo.get_all()
    assert len(result) == 3
    assert {p.payment_id for p in result} == {p.payment_id for p in seeded}


def test_get_all_empty(repo: InMemoryPaymentRepository) -> None:
    """get_all returns empty list when nothing stored."""
    result = repo.get_all()
    assert result == []


# ── BaseRepo: delete ─────────────────────────────────────────────────────────


def test_delete_removes_payment(repo: InMemoryPaymentRepository) -> None:
    """delete removes the payment from the store."""
    seeded = _seed(repo, n=1)
    payment_id = seeded[0].payment_id

    repo.delete(payment_id)
    result = repo.get_by_id(payment_id)

    assert result is None


def test_delete_idempotent(repo: InMemoryPaymentRepository) -> None:
    """delete on non-existent id does not raise."""
    repo.delete(uuid4())  # should not raise
    assert True


# ── BaseRepo: update ─────────────────────────────────────────────────────────


def test_update_returns_true(repo: InMemoryPaymentRepository) -> None:
    """update returns True and changes fields."""
    seeded = _seed(repo, n=1)
    payment = seeded[0]
    updated = payment.model_copy(update={"amount": 2500.0, "active": False})

    result = repo.update(payment.payment_id, updated)

    assert result is True
    stored = repo.get_by_id(payment.payment_id)
    assert stored is not None
    assert stored.amount == 2500.0
    assert stored.active is False


def test_update_non_existent_returns_false(
    repo: InMemoryPaymentRepository,
) -> None:
    """update on non-existent id returns False."""
    payment = _payment()
    result = repo.update(uuid4(), payment)
    assert result is False


# ── BaseRepo: exists ─────────────────────────────────────────────────────────


def test_exists_by_field(repo: InMemoryPaymentRepository) -> None:
    """exists returns True when a matching payment is found."""
    seeded = _seed(repo, n=1)
    payment_id = seeded[0].payment_id

    assert repo.exists({"payment_id": payment_id}) is True


def test_exists_not_found(repo: InMemoryPaymentRepository) -> None:
    """exists returns False when no payment matches."""
    assert repo.exists({"payment_id": uuid4()}) is False


# ── BaseRepo: get_by_ids ─────────────────────────────────────────────────────


def test_get_by_ids_returns_matching(repo: InMemoryPaymentRepository) -> None:
    """get_by_ids returns only payments with matching ids."""
    seeded = _seed(repo, n=3)
    ids = [seeded[0].payment_id, seeded[2].payment_id]

    result = repo.get_by_ids(ids)

    assert len(result) == 2
    assert {p.payment_id for p in result} == set(ids)


def test_get_by_ids_empty_list(repo: InMemoryPaymentRepository) -> None:
    """get_by_ids with empty list returns empty list."""
    result = repo.get_by_ids([])
    assert result == []


# ── _Activatable: activate / inactivate ──────────────────────────────────────


def test_activate_sets_active_true(repo: InMemoryPaymentRepository) -> None:
    """activate sets active=True on a payment."""
    seeded = _seed(repo, n=1)
    payment_id = seeded[0].payment_id

    # First inactivate
    repo.inactivate(payment_id)
    stored = repo.get_by_id(payment_id)
    assert stored is not None
    assert stored.active is False

    # Then activate
    result = repo.activate(payment_id)
    assert result is True

    stored = repo.get_by_id(payment_id)
    assert stored is not None
    assert stored.active is True


def test_inactivate_sets_active_false(repo: InMemoryPaymentRepository) -> None:
    """inactivate sets active=False on a payment."""
    seeded = _seed(repo, n=1)
    payment_id = seeded[0].payment_id

    result = repo.inactivate(payment_id)

    assert result is True
    stored = repo.get_by_id(payment_id)
    assert stored is not None
    assert stored.active is False


def test_activate_non_existent_returns_false(
    repo: InMemoryPaymentRepository,
) -> None:
    """activate on non-existent id returns False."""
    assert repo.activate(uuid4()) is False


def test_inactivate_non_existent_returns_false(
    repo: InMemoryPaymentRepository,
) -> None:
    """inactivate on non-existent id returns False."""
    assert repo.inactivate(uuid4()) is False


# ── PaymentRepoPort custom ───────────────────────────────────────────────────


def test_get_by_claim_id(repo: InMemoryPaymentRepository) -> None:
    """get_by_claim_id returns payments for a specific claim."""
    claim_id = uuid4()
    p1 = _payment(claim_id=claim_id)
    p2 = _payment(claim_id=claim_id)
    p3 = _payment(claim_id=uuid4())  # different claim
    for p in [p1, p2, p3]:
        repo.add(p)

    result = repo.get_by_claim_id(claim_id)

    assert len(result) == 2
    assert all(p.claim_id == claim_id for p in result)


def test_get_by_claim_id_empty(repo: InMemoryPaymentRepository) -> None:
    """get_by_claim_id returns empty list when claim has no payments."""
    _seed(repo, n=2)
    result = repo.get_by_claim_id(uuid4())
    assert result == []


def test_get_by_date_range(repo: InMemoryPaymentRepository) -> None:
    """get_by_date_range returns payments within date range."""
    today = datetime.now()
    old = today - timedelta(days=10)
    very_old = today - timedelta(days=30)

    p1 = _payment(created_date=very_old)  # outside
    p2 = _payment(created_date=old)  # inside
    p3 = _payment(created_date=today)  # inside
    for p in [p1, p2, p3]:
        repo.add(p)

    start = (today - timedelta(days=20)).isoformat()
    end = (today + timedelta(days=1)).isoformat()
    result = repo.get_by_date_range(start, end)

    assert len(result) == 2
    assert p2.payment_id in {r.payment_id for r in result}
    assert p3.payment_id in {r.payment_id for r in result}


def test_get_by_date_range_empty(repo: InMemoryPaymentRepository) -> None:
    """get_by_date_range returns empty list when no match."""
    _seed(repo, n=2)
    start = (datetime.now() - timedelta(days=100)).isoformat()
    end = (datetime.now() - timedelta(days=90)).isoformat()
    result = repo.get_by_date_range(start, end)
    assert result == []


def test_get_by_amount_range(repo: InMemoryPaymentRepository) -> None:
    """get_by_amount_range returns payments within amount range."""
    p1 = _payment(amount=500.0)
    p2 = _payment(amount=1500.0)
    p3 = _payment(amount=3000.0)
    for p in [p1, p2, p3]:
        repo.add(p)

    result = repo.get_by_amount_range(1000.0, 2000.0)

    assert len(result) == 1
    assert result[0].amount == 1500.0


def test_get_by_amount_range_empty(repo: InMemoryPaymentRepository) -> None:
    """get_by_amount_range returns empty list when no match."""
    _seed(repo, n=2)
    result = repo.get_by_amount_range(999999.0, 9999999.0)
    assert result == []


def test_deleteable_returns_true_when_no_nc_payment(
    repo: InMemoryPaymentRepository,
) -> None:
    """deleteable returns True — no NcPayment reference check in in-memory."""
    seeded = _seed(repo, n=1)
    result = repo.deleteable(seeded[0].payment_id)
    assert result is True


def test_inactivatable_returns_true_when_no_nc_payment(
    repo: InMemoryPaymentRepository,
) -> None:
    """inactivatable returns True — no NcPayment reference check in in-memory."""
    seeded = _seed(repo, n=1)
    result = repo.inactivatable(seeded[0].payment_id)
    assert result is True


# ═══════════════════════════════════════════════════════════════════════════════
# InMemoryNcPaymentRepository
# ═══════════════════════════════════════════════════════════════════════════════


@pytest.fixture
def nc_repo() -> InMemoryNcPaymentRepository:
    return InMemoryNcPaymentRepository()


# ── Helpers ──────────────────────────────────────────────────────────────────


def _credit_note(**overrides: object) -> CreditNote:
    defaults: dict[str, object] = {
        "nc_payment_id": uuid4(),
        "payment_id": uuid4(),
        "period_id": uuid4(),
        "delivered": False,
        "active": True,
        "created_date": datetime.now(),
    }
    merged = {**defaults, **overrides}
    return CreditNote(**merged)


def _seed_nc(repo: InMemoryNcPaymentRepository, n: int = 3) -> list[CreditNote]:
    notes = [_credit_note() for _ in range(n)]
    for n in notes:
        repo.add(n)
    return notes


# ── BaseRepo: add / get_by_id / get_all ──────────────────────────────────────


def test_nc_add_and_get_by_id(nc_repo: InMemoryNcPaymentRepository) -> None:
    """add() stores a credit note; get_by_id() retrieves it."""
    note = _credit_note()
    nc_repo.add(note)

    result = nc_repo.get_by_id(note.nc_payment_id)

    assert result is not None
    assert result.nc_payment_id == note.nc_payment_id
    assert result.delivered is False
    assert result.active is True


def test_nc_get_by_id_not_found(nc_repo: InMemoryNcPaymentRepository) -> None:
    """get_by_id returns None for unknown id."""
    result = nc_repo.get_by_id(uuid4())
    assert result is None


def test_nc_get_all_returns_all(nc_repo: InMemoryNcPaymentRepository) -> None:
    """get_all returns every stored credit note."""
    seeded = _seed_nc(nc_repo, n=3)
    result = nc_repo.get_all()
    assert len(result) == 3
    assert {n.nc_payment_id for n in result} == {n.nc_payment_id for n in seeded}


def test_nc_get_all_empty(nc_repo: InMemoryNcPaymentRepository) -> None:
    """get_all returns empty list when nothing stored."""
    result = nc_repo.get_all()
    assert result == []


# ── BaseRepo: delete ─────────────────────────────────────────────────────────


def test_nc_delete_removes(nc_repo: InMemoryNcPaymentRepository) -> None:
    """delete removes the credit note from the store."""
    seeded = _seed_nc(nc_repo, n=1)
    note_id = seeded[0].nc_payment_id
    nc_repo.delete(note_id)
    result = nc_repo.get_by_id(note_id)
    assert result is None


def test_nc_delete_idempotent(nc_repo: InMemoryNcPaymentRepository) -> None:
    """delete on non-existent id does not raise."""
    nc_repo.delete(uuid4())
    assert True


# ── BaseRepo: update ─────────────────────────────────────────────────────────


def test_nc_update_returns_true(nc_repo: InMemoryNcPaymentRepository) -> None:
    """update returns True and changes fields."""
    seeded = _seed_nc(nc_repo, n=1)
    note = seeded[0]
    updated = note.model_copy(update={"delivered": True, "active": False})

    result = nc_repo.update(note.nc_payment_id, updated)

    assert result is True
    stored = nc_repo.get_by_id(note.nc_payment_id)
    assert stored is not None
    assert stored.delivered is True
    assert stored.active is False


def test_nc_update_non_existent_returns_false(
    nc_repo: InMemoryNcPaymentRepository,
) -> None:
    """update on non-existent id returns False."""
    note = _credit_note()
    result = nc_repo.update(uuid4(), note)
    assert result is False


# ── BaseRepo: exists ─────────────────────────────────────────────────────────


def test_nc_exists_by_field(nc_repo: InMemoryNcPaymentRepository) -> None:
    """exists returns True when a matching credit note is found."""
    seeded = _seed_nc(nc_repo, n=1)
    result = nc_repo.exists({"nc_payment_id": seeded[0].nc_payment_id})
    assert result is True


def test_nc_exists_not_found(nc_repo: InMemoryNcPaymentRepository) -> None:
    """exists returns False when no credit note matches."""
    assert nc_repo.exists({"nc_payment_id": uuid4()}) is False


# ── BaseRepo: get_by_ids ─────────────────────────────────────────────────────


def test_nc_get_by_ids_returns_matching(
    nc_repo: InMemoryNcPaymentRepository,
) -> None:
    """get_by_ids returns only credit notes with matching ids."""
    seeded = _seed_nc(nc_repo, n=3)
    ids = [seeded[0].nc_payment_id, seeded[2].nc_payment_id]

    result = nc_repo.get_by_ids(ids)

    assert len(result) == 2
    assert {n.nc_payment_id for n in result} == set(ids)


def test_nc_get_by_ids_empty_list(
    nc_repo: InMemoryNcPaymentRepository,
) -> None:
    """get_by_ids with empty list returns empty list."""
    result = nc_repo.get_by_ids([])
    assert result == []


# ── _Activatable: activate / inactivate ──────────────────────────────────────


def test_nc_activate_sets_active_true(
    nc_repo: InMemoryNcPaymentRepository,
) -> None:
    """activate sets active=True on a credit note."""
    seeded = _seed_nc(nc_repo, n=1)
    note_id = seeded[0].nc_payment_id

    nc_repo.inactivate(note_id)
    stored = nc_repo.get_by_id(note_id)
    assert stored is not None
    assert stored.active is False

    result = nc_repo.activate(note_id)
    assert result is True
    stored = nc_repo.get_by_id(note_id)
    assert stored is not None
    assert stored.active is True


def test_nc_inactivate_sets_active_false(
    nc_repo: InMemoryNcPaymentRepository,
) -> None:
    """inactivate sets active=False on a credit note."""
    seeded = _seed_nc(nc_repo, n=1)
    note_id = seeded[0].nc_payment_id

    result = nc_repo.inactivate(note_id)

    assert result is True
    stored = nc_repo.get_by_id(note_id)
    assert stored is not None
    assert stored.active is False


def test_nc_activate_non_existent_returns_false(
    nc_repo: InMemoryNcPaymentRepository,
) -> None:
    """activate on non-existent id returns False."""
    assert nc_repo.activate(uuid4()) is False


def test_nc_inactivate_non_existent_returns_false(
    nc_repo: InMemoryNcPaymentRepository,
) -> None:
    """inactivate on non-existent id returns False."""
    assert nc_repo.inactivate(uuid4()) is False


# ── NcPaymentRepoPort custom ─────────────────────────────────────────────────


def test_nc_mark_delivered_sets_true(
    nc_repo: InMemoryNcPaymentRepository,
) -> None:
    """mark_delivered sets delivered=True on a credit note."""
    seeded = _seed_nc(nc_repo, n=1)
    note_id = seeded[0].nc_payment_id

    result = nc_repo.mark_delivered(note_id)

    assert result is True
    stored = nc_repo.get_by_id(note_id)
    assert stored is not None
    assert stored.delivered is True


def test_nc_mark_delivered_non_existent_returns_false(
    nc_repo: InMemoryNcPaymentRepository,
) -> None:
    """mark_delivered on non-existent id returns False."""
    assert nc_repo.mark_delivered(uuid4()) is False


def test_nc_get_by_payment_id(nc_repo: InMemoryNcPaymentRepository) -> None:
    """get_by_payment_id returns the credit note for a payment."""
    payment_id = uuid4()
    n1 = _credit_note(payment_id=payment_id)
    n2 = _credit_note(payment_id=uuid4())
    for n in [n1, n2]:
        nc_repo.add(n)

    result = nc_repo.get_by_payment_id(payment_id)

    assert result is not None
    assert result.nc_payment_id == n1.nc_payment_id


def test_nc_get_by_payment_id_not_found(
    nc_repo: InMemoryNcPaymentRepository,
) -> None:
    """get_by_payment_id returns None when no match."""
    _seed_nc(nc_repo, n=2)
    result = nc_repo.get_by_payment_id(uuid4())
    assert result is None


def test_nc_get_by_period_id(nc_repo: InMemoryNcPaymentRepository) -> None:
    """get_by_period_id returns credit notes for a period."""
    period_id = uuid4()
    n1 = _credit_note(period_id=period_id)
    n2 = _credit_note(period_id=period_id)
    n3 = _credit_note(period_id=uuid4())
    for n in [n1, n2, n3]:
        nc_repo.add(n)

    result = nc_repo.get_by_period_id(period_id)

    assert len(result) == 2
    assert all(n.period_id == period_id for n in result)


def test_nc_get_by_period_id_empty(
    nc_repo: InMemoryNcPaymentRepository,
) -> None:
    """get_by_period_id returns empty list when no match."""
    _seed_nc(nc_repo, n=2)
    result = nc_repo.get_by_period_id(uuid4())
    assert result == []


def test_nc_deleteable_returns_true(
    nc_repo: InMemoryNcPaymentRepository,
) -> None:
    """deleteable returns True."""
    seeded = _seed_nc(nc_repo, n=1)
    result = nc_repo.deleteable(seeded[0].nc_payment_id)
    assert result is True
