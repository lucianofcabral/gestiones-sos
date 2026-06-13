"""Unit tests for PeriodRepoPort using InMemoryPeriodRepository."""

from uuid import UUID, uuid4

import pytest

from src.adapters.persistence.inmemory_period_repository import (
    InMemoryPeriodRepository,
)
from src.domain.models.entities import Period


# ── Fixtures ─────────────────────────────────────────────────────────────────


@pytest.fixture
def period_repo() -> InMemoryPeriodRepository:
    return InMemoryPeriodRepository()


# ── Helpers ──────────────────────────────────────────────────────────────────


def _seed_period(
    repo: InMemoryPeriodRepository,
    period_id: UUID | None = None,
    year: int = 2025,
    month: int = 6,
) -> Period:
    pid = period_id or uuid4()
    period = Period(period_id=pid, year=year, month=month)
    repo.add(period)
    return period


# ── BaseRepo: get_by_id ──────────────────────────────────────────────────────


def test_get_by_id_returns_period_when_found(
    period_repo: InMemoryPeriodRepository,
) -> None:
    period = _seed_period(period_repo)

    result = period_repo.get_by_id(period.period_id)

    assert result is not None
    assert result.period_id == period.period_id
    assert result.year == period.year
    assert result.month == period.month


def test_get_by_id_returns_none_when_not_found(
    period_repo: InMemoryPeriodRepository,
) -> None:
    result = period_repo.get_by_id(uuid4())

    assert result is None


# ── BaseRepo: add ────────────────────────────────────────────────────────────


def test_add_stores_period(period_repo: InMemoryPeriodRepository) -> None:
    period = Period(year=2025, month=1, period_id=uuid4())

    result = period_repo.add(period)

    assert result == period
    assert period_repo.get_by_id(period.period_id) == period


# ── BaseRepo: get_all ────────────────────────────────────────────────────────


def test_get_all_returns_all_periods(
    period_repo: InMemoryPeriodRepository,
) -> None:
    p1 = _seed_period(period_repo, year=2025, month=1)
    p2 = _seed_period(period_repo, year=2025, month=2)

    result = period_repo.get_all()

    assert len(result) == 2
    assert p1 in result
    assert p2 in result


def test_get_all_returns_empty_when_no_periods(
    period_repo: InMemoryPeriodRepository,
) -> None:
    result = period_repo.get_all()
    assert result == []


# ── BaseRepo: exists ─────────────────────────────────────────────────────────


def test_exists_returns_true_when_match(
    period_repo: InMemoryPeriodRepository,
) -> None:
    _seed_period(period_repo, year=2025, month=6)

    assert period_repo.exists({"year": 2025, "month": 6}) is True


def test_exists_returns_false_when_no_match(
    period_repo: InMemoryPeriodRepository,
) -> None:
    _seed_period(period_repo, year=2025, month=6)

    assert period_repo.exists({"year": 2024, "month": 1}) is False


# ── BaseRepo: update ─────────────────────────────────────────────────────────


def test_update_returns_true_and_modifies(
    period_repo: InMemoryPeriodRepository,
) -> None:
    period = _seed_period(period_repo, year=2025, month=6)
    updated = Period(period_id=period.period_id, year=2025, month=7)

    result = period_repo.update(period.period_id, updated)

    assert result is True
    stored = period_repo.get_by_id(period.period_id)
    assert stored is not None
    assert stored.month == 7


def test_update_returns_false_when_not_found(
    period_repo: InMemoryPeriodRepository,
) -> None:
    p = Period(year=2025, month=1)
    result = period_repo.update(p.period_id, p)
    assert result is False


# ── BaseRepo: delete ─────────────────────────────────────────────────────────


def test_delete_removes_period(period_repo: InMemoryPeriodRepository) -> None:
    period = _seed_period(period_repo)

    period_repo.delete(period.period_id)

    assert period_repo.get_by_id(period.period_id) is None


def test_delete_nonexistent_does_nothing(
    period_repo: InMemoryPeriodRepository,
) -> None:
    period_repo.delete(uuid4())  # should not raise


# ── BaseRepo: get_by_ids ─────────────────────────────────────────────────────


def test_get_by_ids_returns_matching(
    period_repo: InMemoryPeriodRepository,
) -> None:
    p1 = _seed_period(period_repo)
    p2 = _seed_period(period_repo)
    p3 = _seed_period(period_repo)

    result = period_repo.get_by_ids([p1.period_id, p3.period_id])

    assert len(result) == 2
    assert p1 in result
    assert p3 in result
    assert p2 not in result


def test_get_by_ids_returns_empty_when_none_match(
    period_repo: InMemoryPeriodRepository,
) -> None:
    _seed_period(period_repo)
    result = period_repo.get_by_ids([uuid4(), uuid4()])
    assert result == []


# ── PeriodRepoPort: get_by_year_month ────────────────────────────────────────


def test_get_by_year_month_returns_period_when_found(
    period_repo: InMemoryPeriodRepository,
) -> None:
    _seed_period(period_repo, year=2025, month=6)

    result = period_repo.get_by_year_month(2025, 6)

    assert result is not None
    assert result.year == 2025
    assert result.month == 6


def test_get_by_year_month_returns_none_when_not_found(
    period_repo: InMemoryPeriodRepository,
) -> None:
    result = period_repo.get_by_year_month(2025, 6)
    assert result is None


# ── PeriodRepoPort: get_n_last ───────────────────────────────────────────────


def test_get_n_last_returns_n_most_recent(
    period_repo: InMemoryPeriodRepository,
) -> None:
    _seed_period(period_repo, year=2024, month=12)
    _seed_period(period_repo, year=2025, month=1)
    _seed_period(period_repo, year=2025, month=2)

    result = period_repo.get_n_last(2)

    assert len(result) == 2
    assert result[0].year == 2025 and result[0].month == 2
    assert result[1].year == 2025 and result[1].month == 1


def test_get_n_last_with_none_returns_all_sorted(
    period_repo: InMemoryPeriodRepository,
) -> None:
    _seed_period(period_repo, year=2024, month=12)
    _seed_period(period_repo, year=2025, month=1)

    result = period_repo.get_n_last(None)

    assert len(result) == 2


# ── PeriodRepoPort: get_total_billing_by_year_month ──────────────────────────


def test_get_total_billing_returns_zero_when_no_invoices(
    period_repo: InMemoryPeriodRepository,
) -> None:
    result = period_repo.get_total_billing_by_year_month(2025, 6)
    assert result == 0.0
