"""Unit tests for Periods CRUD use cases using in-memory implementations."""

from uuid import UUID, uuid4

import pytest

from src.adapters.persistence.inmemory_billing_repository import (
    InMemoryBillingRepository,
)
from src.adapters.persistence.inmemory_ncpayment_repository import (
    InMemoryNcPaymentRepository,
)
from src.adapters.persistence.inmemory_period_repository import (
    InMemoryPeriodRepository,
)
from src.application.use_cases.periods.crear_periodo import CrearPeriodo
from src.application.use_cases.periods.eliminar_periodo import EliminarPeriodo
from src.application.use_cases.periods.listar_periodos import ListarPeriodos
from src.domain.models.entities import CreditNote, Invoice, Period


# ═══════════════════════════════════════════════════════════════════════════════
# Fixtures
# ═══════════════════════════════════════════════════════════════════════════════


@pytest.fixture
def period_repo() -> InMemoryPeriodRepository:
    return InMemoryPeriodRepository()


@pytest.fixture
def billing_repo() -> InMemoryBillingRepository:
    return InMemoryBillingRepository()


@pytest.fixture
def nc_payment_repo() -> InMemoryNcPaymentRepository:
    return InMemoryNcPaymentRepository()


# ═══════════════════════════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════════════════════════


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


def _seed_invoice(
    repo: InMemoryBillingRepository,
    period_id: UUID,
    invoice_id: UUID | None = None,
) -> Invoice:
    iid = invoice_id or uuid4()
    inv = Invoice(
        invoice_id=iid,
        invoice_number="F001",
        period_id=period_id,
        emited_date="2025-06-15",
        amount=1000.0,
    )
    repo.add(inv)
    return inv


def _seed_credit_note(
    repo: InMemoryNcPaymentRepository,
    period_id: UUID,
    nc_id: UUID | None = None,
) -> CreditNote:
    nid = nc_id or uuid4()
    nc = CreditNote(
        nc_payment_id=nid,
        payment_id=uuid4(),
        period_id=period_id,
    )
    repo.add(nc)
    return nc


# ═══════════════════════════════════════════════════════════════════════════════
# CrearPeriodo Tests
# ═══════════════════════════════════════════════════════════════════════════════


class TestCrearPeriodo:
    """Tests for CrearPeriodo use case."""

    def test_creates_new_period(self, period_repo: InMemoryPeriodRepository) -> None:
        uc = CrearPeriodo(period_repo)
        inp = CrearPeriodo.Input(year=2025, month=6)

        result = uc.execute(inp)

        assert result.period is not None
        assert result.period.year == 2025
        assert result.period.month == 6
        assert result.period.period_name == "Junio 2025"
        assert result.period.period_number == 202506
        # Verify it was persisted
        stored = period_repo.get_by_id(result.period.period_id)
        assert stored is not None
        assert stored.year == 2025
        assert stored.month == 6

    def test_duplicate_year_month_raises_error(
        self, period_repo: InMemoryPeriodRepository
    ) -> None:
        _seed_period(period_repo, year=2025, month=6)
        uc = CrearPeriodo(period_repo)
        inp = CrearPeriodo.Input(year=2025, month=6)

        with pytest.raises(ValueError, match="Ya existe un período para"):
            uc.execute(inp)

        # Verify only one period exists
        assert len(period_repo.get_all()) == 1


# ═══════════════════════════════════════════════════════════════════════════════
# ListarPeriodos Tests
# ═══════════════════════════════════════════════════════════════════════════════


class TestListarPeriodos:
    """Tests for ListarPeriodos use case."""

    def test_returns_all_periods_ordered_by_recency(
        self, period_repo: InMemoryPeriodRepository
    ) -> None:
        _seed_period(period_repo, year=2024, month=6)
        _seed_period(period_repo, year=2024, month=3)
        _seed_period(period_repo, year=2023, month=12)
        uc = ListarPeriodos(period_repo)

        result = uc.execute()

        assert len(result.periods) == 3
        assert result.periods[0].year == 2024 and result.periods[0].month == 6
        assert result.periods[1].year == 2024 and result.periods[1].month == 3
        assert result.periods[2].year == 2023 and result.periods[2].month == 12

    def test_returns_empty_list_when_no_periods(
        self, period_repo: InMemoryPeriodRepository
    ) -> None:
        uc = ListarPeriodos(period_repo)

        result = uc.execute()

        assert result.periods == []


# ═══════════════════════════════════════════════════════════════════════════════
# EliminarPeriodo Tests
# ═══════════════════════════════════════════════════════════════════════════════


class TestEliminarPeriodo:
    """Tests for EliminarPeriodo use case."""

    def test_deletes_period_with_no_dependents(
        self,
        period_repo: InMemoryPeriodRepository,
        billing_repo: InMemoryBillingRepository,
        nc_payment_repo: InMemoryNcPaymentRepository,
    ) -> None:
        period = _seed_period(period_repo)
        uc = EliminarPeriodo(period_repo, billing_repo, nc_payment_repo)
        inp = EliminarPeriodo.Input(period_id=period.period_id)

        result = uc.execute(inp)

        assert result.deleted is True
        assert period_repo.get_by_id(period.period_id) is None

    def test_nonexistent_period_returns_false(
        self,
        period_repo: InMemoryPeriodRepository,
        billing_repo: InMemoryBillingRepository,
        nc_payment_repo: InMemoryNcPaymentRepository,
    ) -> None:
        uc = EliminarPeriodo(period_repo, billing_repo, nc_payment_repo)
        inp = EliminarPeriodo.Input(period_id=uuid4())

        result = uc.execute(inp)

        assert result.deleted is False

    def test_period_with_invoices_raises_error(
        self,
        period_repo: InMemoryPeriodRepository,
        billing_repo: InMemoryBillingRepository,
        nc_payment_repo: InMemoryNcPaymentRepository,
    ) -> None:
        period = _seed_period(period_repo)
        _seed_invoice(billing_repo, period_id=period.period_id)
        uc = EliminarPeriodo(period_repo, billing_repo, nc_payment_repo)
        inp = EliminarPeriodo.Input(period_id=period.period_id)

        with pytest.raises(ValueError, match="facturas asociadas"):
            uc.execute(inp)

        # Period should still exist
        assert period_repo.get_by_id(period.period_id) is not None

    def test_period_with_credit_notes_raises_error(
        self,
        period_repo: InMemoryPeriodRepository,
        billing_repo: InMemoryBillingRepository,
        nc_payment_repo: InMemoryNcPaymentRepository,
    ) -> None:
        period = _seed_period(period_repo)
        _seed_credit_note(nc_payment_repo, period_id=period.period_id)
        uc = EliminarPeriodo(period_repo, billing_repo, nc_payment_repo)
        inp = EliminarPeriodo.Input(period_id=period.period_id)

        with pytest.raises(ValueError, match="notas de crédito asociadas"):
            uc.execute(inp)

        # Period should still exist
        assert period_repo.get_by_id(period.period_id) is not None
