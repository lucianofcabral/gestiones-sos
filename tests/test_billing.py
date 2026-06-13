"""Unit tests for Invoice repos and billing use cases using in-memory implementations."""

from datetime import datetime
from uuid import UUID, uuid4

import pytest

from src.adapters.persistence.inmemory_billing_repository import (
    InMemoryBillingRepository,
)
from src.adapters.persistence.inmemory_document_repository import (
    InMemoryDocumentRepository,
)
from src.adapters.persistence.inmemory_period_repository import (
    InMemoryPeriodRepository,
)
from src.application.use_cases.billing.eliminar_factura import EliminarFactura
from src.application.use_cases.billing.obtener_factura import ObtenerFactura
from src.application.use_cases.billing.obtener_facturas import ObtenerFacturas
from src.application.use_cases.billing.obtener_total_facturacion import (
    ObtenerTotalFacturacion,
)
from src.application.use_cases.billing.registrar_factura import RegistrarFactura
from src.domain.models.entities import Invoice, Period


# ═══════════════════════════════════════════════════════════════════════════════
# Fixtures
# ═══════════════════════════════════════════════════════════════════════════════


@pytest.fixture
def billing_repo() -> InMemoryBillingRepository:
    return InMemoryBillingRepository()


@pytest.fixture
def document_repo() -> InMemoryDocumentRepository:
    return InMemoryDocumentRepository()


@pytest.fixture
def period_repo_with_invoices(
    billing_repo: InMemoryBillingRepository,
) -> InMemoryPeriodRepository:
    return InMemoryPeriodRepository(invoice_store=billing_repo._store)


# ═══════════════════════════════════════════════════════════════════════════════
# Seed helpers
# ═══════════════════════════════════════════════════════════════════════════════


def _seed_invoice(
    repo: InMemoryBillingRepository,
    invoice_id: UUID | None = None,
    invoice_number: str = "F001-2024",
    period_id: UUID | None = None,
    amount: float = 1000.00,
    emited_date: datetime | None = None,
) -> Invoice:
    iid = invoice_id or uuid4()
    pid = period_id or uuid4()
    inv = Invoice(
        invoice_id=iid,
        invoice_number=invoice_number,
        period_id=pid,
        emited_date=emited_date or datetime(2024, 6, 15),
        amount=amount,
    )
    repo.add(inv)
    return inv


def _seed_period(
    repo: InMemoryPeriodRepository,
    period_id: UUID | None = None,
    year: int = 2024,
    month: int = 6,
) -> Period:
    pid = period_id or uuid4()
    period = Period(period_id=pid, year=year, month=month)
    repo.add(period)
    return period


# ═══════════════════════════════════════════════════════════════════════════════
# InMemoryBillingRepository Tests
# ═══════════════════════════════════════════════════════════════════════════════


class TestBillingRepo:
    """Tests for InMemoryBillingRepository — BaseRepo + BillingRepoPort."""

    # ── BaseRepo: get_by_id ────────────────────────────────────────────────

    def test_get_by_id_returns_invoice_when_found(
        self, billing_repo: InMemoryBillingRepository
    ) -> None:
        inv = _seed_invoice(billing_repo)

        result = billing_repo.get_by_id(inv.invoice_id)

        assert result is not None
        assert result.invoice_id == inv.invoice_id

    def test_get_by_id_returns_none_when_not_found(
        self, billing_repo: InMemoryBillingRepository
    ) -> None:
        result = billing_repo.get_by_id(uuid4())
        assert result is None

    # ── BaseRepo: add ──────────────────────────────────────────────────────

    def test_add_stores_invoice(self, billing_repo: InMemoryBillingRepository) -> None:
        inv = Invoice(
            invoice_number="F001-2024",
            period_id=uuid4(),
            emited_date=datetime(2024, 6, 15),
            amount=1500.00,
        )

        result = billing_repo.add(inv)

        assert result == inv
        assert billing_repo.get_by_id(inv.invoice_id) == inv

    # ── BaseRepo: get_all ──────────────────────────────────────────────────

    def test_get_all_returns_all_invoices(
        self, billing_repo: InMemoryBillingRepository
    ) -> None:
        i1 = _seed_invoice(billing_repo, invoice_number="F001")
        i2 = _seed_invoice(billing_repo, invoice_number="F002")

        result = billing_repo.get_all()

        assert len(result) == 2
        assert i1 in result
        assert i2 in result

    def test_get_all_returns_empty_when_no_invoices(
        self, billing_repo: InMemoryBillingRepository
    ) -> None:
        result = billing_repo.get_all()
        assert result == []

    # ── BaseRepo: exists ───────────────────────────────────────────────────

    def test_exists_returns_true_when_match(
        self, billing_repo: InMemoryBillingRepository
    ) -> None:
        _seed_invoice(billing_repo, invoice_number="F001")

        assert billing_repo.exists({"invoice_number": "F001"}) is True

    def test_exists_returns_false_when_no_match(
        self, billing_repo: InMemoryBillingRepository
    ) -> None:
        _seed_invoice(billing_repo, invoice_number="F001")

        assert billing_repo.exists({"invoice_number": "F002"}) is False

    # ── BaseRepo: update ───────────────────────────────────────────────────

    def test_update_returns_true_and_modifies(
        self, billing_repo: InMemoryBillingRepository
    ) -> None:
        inv = _seed_invoice(billing_repo, amount=500.00)
        updated = Invoice(
            invoice_id=inv.invoice_id,
            invoice_number=inv.invoice_number,
            period_id=inv.period_id,
            emited_date=inv.emited_date,
            amount=999.00,
            created_at=inv.created_at,
        )

        result = billing_repo.update(inv.invoice_id, updated)

        assert result is True
        stored = billing_repo.get_by_id(inv.invoice_id)
        assert stored is not None
        assert stored.amount == 999.00

    def test_update_returns_false_when_not_found(
        self, billing_repo: InMemoryBillingRepository
    ) -> None:
        inv = Invoice(
            invoice_number="Ghost",
            period_id=uuid4(),
            emited_date=datetime(2024, 6, 15),
            amount=100.00,
        )
        result = billing_repo.update(inv.invoice_id, inv)
        assert result is False

    # ── BaseRepo: delete ───────────────────────────────────────────────────

    def test_delete_removes_invoice(
        self, billing_repo: InMemoryBillingRepository
    ) -> None:
        inv = _seed_invoice(billing_repo)

        billing_repo.delete(inv.invoice_id)

        assert billing_repo.get_by_id(inv.invoice_id) is None

    def test_delete_nonexistent_does_nothing(
        self, billing_repo: InMemoryBillingRepository
    ) -> None:
        billing_repo.delete(uuid4())  # should not raise

    # ── BaseRepo: get_by_ids ───────────────────────────────────────────────

    def test_get_by_ids_returns_matching(
        self, billing_repo: InMemoryBillingRepository
    ) -> None:
        i1 = _seed_invoice(billing_repo)
        i2 = _seed_invoice(billing_repo)
        i3 = _seed_invoice(billing_repo)

        result = billing_repo.get_by_ids([i1.invoice_id, i3.invoice_id])

        assert len(result) == 2
        assert i1 in result
        assert i3 in result
        assert i2 not in result

    def test_get_by_ids_returns_empty_when_none_match(
        self, billing_repo: InMemoryBillingRepository
    ) -> None:
        _seed_invoice(billing_repo)
        result = billing_repo.get_by_ids([uuid4(), uuid4()])
        assert result == []

    # ── BillingRepoPort: get_by_period_id ──────────────────────────────────

    def test_get_by_period_id_returns_invoices_for_period(
        self, billing_repo: InMemoryBillingRepository
    ) -> None:
        pid_a = uuid4()
        pid_b = uuid4()
        inv_a1 = _seed_invoice(billing_repo, invoice_number="A1", period_id=pid_a)
        _seed_invoice(billing_repo, invoice_number="A2", period_id=pid_a)
        _seed_invoice(billing_repo, invoice_number="B1", period_id=pid_b)

        result = billing_repo.get_by_period_id(pid_a)

        assert len(result) == 2
        assert inv_a1 in result

    def test_get_by_period_id_returns_empty_when_no_invoices(
        self, billing_repo: InMemoryBillingRepository
    ) -> None:
        result = billing_repo.get_by_period_id(uuid4())
        assert result == []

    # ── _DocReachable stubs ────────────────────────────────────────────────

    def test_get_by_document_id_returns_empty_list(
        self, billing_repo: InMemoryBillingRepository
    ) -> None:
        _seed_invoice(billing_repo)
        result = billing_repo.get_by_document_id(uuid4())
        assert result == []

    def test_get_by_document_returns_empty_list(
        self, billing_repo: InMemoryBillingRepository
    ) -> None:
        _seed_invoice(billing_repo)
        result = billing_repo.get_by_document(b"some content")
        assert result == []


# ═══════════════════════════════════════════════════════════════════════════════
# RegistrarFactura Use Case Tests
# ═══════════════════════════════════════════════════════════════════════════════


class TestRegistrarFactura:
    """Tests for RegistrarFactura use case."""

    def test_creates_new_invoice(self, billing_repo: InMemoryBillingRepository) -> None:
        uc = RegistrarFactura(billing_repo)
        inp = uc.Input(
            invoice_number="F001-2024",
            period_id=uuid4(),
            emited_date=datetime(2024, 6, 15),
            amount=1500.00,
        )

        result = uc.execute(inp)

        assert result.invoice is not None
        assert result.invoice.invoice_number == "F001-2024"
        assert result.invoice.amount == 1500.00
        assert billing_repo.get_by_id(result.invoice.invoice_id) is not None


# ═══════════════════════════════════════════════════════════════════════════════
# ObtenerFacturas Use Case Tests
# ═══════════════════════════════════════════════════════════════════════════════


class TestObtenerFacturas:
    """Tests for ObtenerFacturas use case."""

    def test_get_all_returns_all_invoices(
        self, billing_repo: InMemoryBillingRepository
    ) -> None:
        _seed_invoice(billing_repo, invoice_number="F001")
        _seed_invoice(billing_repo, invoice_number="F002")
        uc = ObtenerFacturas(billing_repo)

        result = uc.execute()

        assert len(result) == 2

    def test_get_all_returns_empty_when_no_invoices(
        self, billing_repo: InMemoryBillingRepository
    ) -> None:
        uc = ObtenerFacturas(billing_repo)

        result = uc.execute()

        assert result == []

    def test_por_periodo_returns_filtered(
        self, billing_repo: InMemoryBillingRepository
    ) -> None:
        pid = uuid4()
        _seed_invoice(billing_repo, invoice_number="F001", period_id=pid)
        _seed_invoice(billing_repo, invoice_number="F002")
        uc = ObtenerFacturas(billing_repo)

        result = uc.por_periodo(pid)

        assert len(result) == 1
        assert result[0].invoice_number == "F001"

    def test_por_periodo_returns_empty_when_no_match(
        self, billing_repo: InMemoryBillingRepository
    ) -> None:
        _seed_invoice(billing_repo)
        uc = ObtenerFacturas(billing_repo)

        result = uc.por_periodo(uuid4())

        assert result == []


# ═══════════════════════════════════════════════════════════════════════════════
# ObtenerFactura Use Case Tests
# ═══════════════════════════════════════════════════════════════════════════════


class TestObtenerFactura:
    """Tests for ObtenerFactura use case."""

    def test_returns_invoice_when_found(
        self, billing_repo: InMemoryBillingRepository
    ) -> None:
        inv = _seed_invoice(billing_repo)
        uc = ObtenerFactura(billing_repo)

        result = uc.execute(inv.invoice_id)

        assert result is not None
        assert result.invoice_id == inv.invoice_id

    def test_returns_none_when_not_found(
        self, billing_repo: InMemoryBillingRepository
    ) -> None:
        uc = ObtenerFactura(billing_repo)

        result = uc.execute(uuid4())

        assert result is None


# ═══════════════════════════════════════════════════════════════════════════════
# EliminarFactura Use Case Tests
# ═══════════════════════════════════════════════════════════════════════════════


class TestEliminarFactura:
    """Tests for EliminarFactura use case."""

    def test_delete_invoice_with_no_documents(
        self,
        billing_repo: InMemoryBillingRepository,
        document_repo: InMemoryDocumentRepository,
    ) -> None:
        inv = _seed_invoice(billing_repo)
        uc = EliminarFactura(billing_repo, document_repo)

        result = uc.execute(inv.invoice_id)

        assert result is True
        assert billing_repo.get_by_id(inv.invoice_id) is None

    def test_delete_nonexistent_invoice_returns_false(
        self,
        billing_repo: InMemoryBillingRepository,
        document_repo: InMemoryDocumentRepository,
    ) -> None:
        uc = EliminarFactura(billing_repo, document_repo)

        result = uc.execute(uuid4())

        assert result is False

    def test_delete_invoice_with_documents_raises_error(
        self,
        billing_repo: InMemoryBillingRepository,
        document_repo: InMemoryDocumentRepository,
    ) -> None:
        invoice_id = uuid4()
        _seed_invoice(billing_repo, invoice_id=invoice_id)

        # Mock get_by_billing_id to simulate a document linked to this invoice

        def _mock_get_by_billing_id(billing_id: UUID) -> object:
            if billing_id == invoice_id:
                from src.domain.models.entities import Document

                return Document(
                    document_id=uuid4(),
                    document_hash="abc123",
                    type="pdf",
                    name="test.pdf",
                    size=100,
                )
            return None

        document_repo.get_by_billing_id = _mock_get_by_billing_id  # type: ignore[assignment]
        uc = EliminarFactura(billing_repo, document_repo)

        with pytest.raises(ValueError, match="documentos asociados"):
            uc.execute(invoice_id)

        # Invoice should still exist
        assert billing_repo.get_by_id(invoice_id) is not None


# ═══════════════════════════════════════════════════════════════════════════════
# ObtenerTotalFacturacion Use Case Tests
# ═══════════════════════════════════════════════════════════════════════════════


class TestObtenerTotalFacturacion:
    """Tests for ObtenerTotalFacturacion use case."""

    def test_returns_sum_of_invoices_for_period(
        self,
        billing_repo: InMemoryBillingRepository,
        period_repo_with_invoices: InMemoryPeriodRepository,
    ) -> None:
        pid = uuid4()
        _seed_period(period_repo_with_invoices, period_id=pid, year=2024, month=6)
        _seed_invoice(billing_repo, period_id=pid, amount=1000.00)
        _seed_invoice(billing_repo, period_id=pid, amount=500.00)
        uc = ObtenerTotalFacturacion(period_repo_with_invoices)

        result = uc.execute(2024, 6)

        assert result == 1500.00

    def test_returns_zero_when_no_invoices(
        self,
        billing_repo: InMemoryBillingRepository,
        period_repo_with_invoices: InMemoryPeriodRepository,
    ) -> None:
        pid = uuid4()
        _seed_period(period_repo_with_invoices, period_id=pid, year=2024, month=7)
        uc = ObtenerTotalFacturacion(period_repo_with_invoices)

        result = uc.execute(2024, 7)

        assert result == 0.0

    def test_returns_sum_only_for_matching_year_month(
        self,
        billing_repo: InMemoryBillingRepository,
        period_repo_with_invoices: InMemoryPeriodRepository,
    ) -> None:
        pid_jun = uuid4()
        pid_jul = uuid4()
        _seed_period(period_repo_with_invoices, period_id=pid_jun, year=2024, month=6)
        _seed_period(period_repo_with_invoices, period_id=pid_jul, year=2024, month=7)
        _seed_invoice(billing_repo, period_id=pid_jun, amount=1000.00)
        _seed_invoice(billing_repo, period_id=pid_jul, amount=2000.00)
        uc = ObtenerTotalFacturacion(period_repo_with_invoices)

        result = uc.execute(2024, 6)

        assert result == 1000.00
