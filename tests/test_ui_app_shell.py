"""Tests for UI App Shell — auth guard, layout, home metrics, and placeholder pages.

NOTE: NiceGUI's ``app.storage.user`` is a property that raises ``RuntimeError``
if ``Storage.secret`` is not set. All tests that interact with storage set
``Storage.secret`` at the module level to avoid this.
"""

from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest

# ── Global setup: prevent RuntimeError from app.storage.user ─────────────────
from nicegui.storage import Storage  # noqa: E402

Storage.secret = "test-secret"

from src.adapters.persistence.inmemory_claim_repository import InMemoryClaimRepository  # noqa: E402
from src.adapters.persistence.inmemory_payment_repository import (
    InMemoryPaymentRepository,
)  # noqa: E402
from src.adapters.persistence.inmemory_period_repository import InMemoryPeriodRepository  # noqa: E402
from src.domain.models.entities import Claim, Payment, Period  # noqa: E402
from src.ui.components.shell import AppShell  # noqa: E402


# ═══════════════════════════════════════════════════════════════════════════════
# Task 4.1 — AppShell auth guard
# ═══════════════════════════════════════════════════════════════════════════════


class TestAuthGuard:
    """AppShell redirects when no token; renders layout when authenticated."""

    def test_redirect_when_no_token(self):
        """GIVEN no token in app.storage.user WHEN AppShell enters THEN ui.navigate.to(/login)."""
        shell = AppShell()
        mock_storage = MagicMock()
        mock_storage.user = {}
        with (
            patch("src.ui.components.shell.app.storage", mock_storage),
            patch("src.ui.components.shell.ui.navigate.to") as mock_navigate,
        ):
            shell.__enter__()
            mock_navigate.assert_called_once_with("/login")

    def test_header_and_sidebar_when_authenticated(self):
        """GIVEN a token WHEN AppShell enters THEN dark mode + header + sidebar render."""
        shell = AppShell()
        mock_storage = MagicMock()
        mock_storage.user = {"token": "abc", "user_name": "Test User"}
        with (
            patch("src.ui.components.shell.app.storage", mock_storage),
            patch("src.ui.components.shell.ui.open") as mock_open,
            patch("src.ui.components.shell.ui.dark_mode") as mock_dark,
            patch("src.ui.components.shell.ui.header") as mock_header,
            patch("src.ui.components.shell.ui.left_drawer") as mock_drawer,
            patch("src.ui.components.shell.ui.link"),
            patch("src.ui.components.shell.ui.row"),
            patch("src.ui.components.shell.ui.column"),
            patch("src.ui.components.shell.ui.label"),
            patch("src.ui.components.shell.ui.icon"),
            patch("src.ui.components.shell.ui.button"),
        ):
            shell.__enter__()
            mock_open.assert_not_called()
            mock_dark.return_value.enable.assert_called_once()
            mock_header.assert_called_once()
            mock_drawer.assert_called_once()

    def test_nav_items_returned(self):
        """_nav_items returns the expected set of navigation items."""
        items = AppShell._nav_items()
        targets = {t for _, t, _ in items}
        assert "/" in targets
        assert "/documentos" in targets
        assert "/gestiones" in targets
        assert "/pagos" in targets
        assert "/periodos" in targets
        assert "/catalogos" in targets
        assert "/grupos" in targets
        assert "/reportes" in targets
        assert "/facturas" in targets
        assert len(items) == 9

    def test_logout_clears_user_and_navigates(self):
        """_logout clears app.storage.user and navigates to /login."""
        mock_storage = MagicMock()
        with (
            patch("src.ui.components.shell.app.storage", mock_storage),
            patch("src.ui.components.shell.ui.navigate.to") as mock_nav,
        ):
            import anyio

            anyio.run(AppShell._logout)

            mock_storage.user.clear.assert_called_once()
            mock_nav.assert_called_once_with("/login")


# ═══════════════════════════════════════════════════════════════════════════════
# Task 4.2 — Home page metrics
# ═══════════════════════════════════════════════════════════════════════════════


@pytest.fixture
def claim_repo():
    return InMemoryClaimRepository()


@pytest.fixture
def payment_repo():
    return InMemoryPaymentRepository()


@pytest.fixture
def period_repo():
    return InMemoryPeriodRepository()


def _seed_claims(repo: InMemoryClaimRepository, n: int) -> list[Claim]:
    now = datetime.now()
    claims = []
    for i in range(n):
        claim = Claim(
            claim_id=uuid4(),
            claim_kind_id=uuid4(),
            group_id=uuid4(),
            claimer_name=f"Reclamante {i}",
            policy_number=f"POL-{i:03d}",
            plate=f"ABC-{i:03d}",
            solved=(i % 2 == 0),  # even = solved, odd = pending
            created_at=now - timedelta(hours=i),
        )
        repo.add(claim)
        claims.append(claim)
    return claims


def _seed_payments(
    repo: InMemoryPaymentRepository, active_count: int, inactive_count: int
) -> list[Payment]:
    payments = []
    for _ in range(active_count):
        p = Payment(
            payment_id=uuid4(),
            claim_id=uuid4(),
            payer_id=uuid4(),
            payee_id=uuid4(),
            payment_via_id=uuid4(),
            amount=1000.0,
            active=True,
        )
        repo.add(p)
        payments.append(p)
    for _ in range(inactive_count):
        p = Payment(
            payment_id=uuid4(),
            claim_id=uuid4(),
            payer_id=uuid4(),
            payee_id=uuid4(),
            payment_via_id=uuid4(),
            amount=500.0,
            active=False,
        )
        repo.add(p)
        payments.append(p)
    return payments


def _seed_period(repo: InMemoryPeriodRepository, year: int, month: int) -> Period:
    period = Period(year=year, month=month)
    repo.add(period)
    return period


class TestHomeMetrics:
    """Verify metrics data aggregation with InMemory repos."""

    def test_total_claims_and_recent_five(self, claim_repo):
        """GIVEN 8 claims WHEN aggregated THEN total=8 and recent=5."""
        _seed_claims(claim_repo, n=8)
        all_claims = claim_repo.get_all()
        assert len(all_claims) == 8

        recent = sorted(all_claims, key=lambda c: c.created_at, reverse=True)[:5]
        assert len(recent) == 5
        # Most recent first (lowest index in seed = newest)
        assert recent[0].claimer_name == "Reclamante 0"

    def test_recent_fewer_than_five(self, claim_repo):
        """GIVEN 3 claims WHEN aggregated THEN all 3 are shown."""
        _seed_claims(claim_repo, n=3)
        all_claims = claim_repo.get_all()
        recent = sorted(all_claims, key=lambda c: c.created_at, reverse=True)[:5]
        assert len(recent) == 3

    def test_empty_claims(self, claim_repo):
        """GIVEN 0 claims THEN total=0 and empty state."""
        all_claims = claim_repo.get_all()
        assert len(all_claims) == 0

    def test_pending_sos_count(self, claim_repo):
        """GIVEN claims with mixed solved status THEN pending SOS = unsolved count."""
        _seed_claims(claim_repo, n=5)
        all_claims = claim_repo.get_all()
        pending = sum(1 for c in all_claims if not c.solved)
        # odd indices = not solved => 2 claims (index 1, 3)
        assert pending == 2

    def test_all_claims_solved(self, claim_repo):
        """GIVEN all claims solved THEN pending SOS = 0."""
        for i in range(3):
            claim_repo.add(
                Claim(
                    claim_id=uuid4(),
                    claim_kind_id=uuid4(),
                    group_id=uuid4(),
                    claimer_name=f"R{i}",
                    policy_number="POL-001",
                    plate="ABC-123",
                    solved=True,
                )
            )
        all_claims = claim_repo.get_all()
        pending = sum(1 for c in all_claims if not c.solved)
        assert pending == 0

    def test_active_payments(self, payment_repo):
        """GIVEN mixed active/inactive payments THEN count only active."""
        _seed_payments(payment_repo, active_count=3, inactive_count=2)
        all_payments = payment_repo.get_all()
        active = sum(1 for p in all_payments if p.active)
        assert active == 3

    def test_no_active_payments(self, payment_repo):
        """GIVEN all payments inactive THEN active count = 0."""
        _seed_payments(payment_repo, active_count=0, inactive_count=2)
        all_payments = payment_repo.get_all()
        active = sum(1 for p in all_payments if p.active)
        assert active == 0

    def test_current_period(self, period_repo):
        """GIVEN a period exists THEN current period name is returned."""
        _seed_period(period_repo, year=2026, month=6)
        periods = period_repo.get_n_last(1)
        assert len(periods) == 1
        assert periods[0].period_name == "Junio 2026"

    def test_no_period(self, period_repo):
        """GIVEN no periods THEN get_n_last returns empty list."""
        periods = period_repo.get_n_last(1)
        assert periods == []

    def test_multiple_periods_returns_newest(self, period_repo):
        """GIVEN multiple periods THEN get_n_last(1) returns the newest."""
        _seed_period(period_repo, year=2024, month=1)
        _seed_period(period_repo, year=2026, month=6)
        _seed_period(period_repo, year=2025, month=12)
        periods = period_repo.get_n_last(1)
        assert len(periods) == 1
        assert periods[0].period_name == "Junio 2026"


class TestHomeMetricsWithContainer:
    """Verify metrics flow through Container with InMemory repos and mocked UI."""

    def test_metrics_render_with_data(self, claim_repo, payment_repo, period_repo):
        """GIVEN data in all repos WHEN render_metrics called THEN no errors."""
        _seed_claims(claim_repo, n=5)
        _seed_payments(payment_repo, active_count=3, inactive_count=1)
        _seed_period(period_repo, year=2026, month=6)

        from src.ui.pages.home import _render_metrics

        with (
            patch("src.ui.pages.home.ui.label"),
            patch("src.ui.pages.home.ui.column"),
            patch("src.ui.pages.home.ui.card"),
            patch("src.ui.pages.home.ui.row"),
            patch("src.ui.pages.home.ui.table") as mock_table,
            patch("src.ui.pages.home.ui.icon"),
        ):
            _render_metrics(
                claim_repo.get_all(), payment_repo.get_all(), period_repo.get_n_last(1)
            )

        # Should have rendered a table (claims exist)
        mock_table.assert_called_once()

    def test_metrics_empty_state(self, claim_repo, payment_repo, period_repo):
        """GIVEN empty repos WHEN render_metrics called THEN empty state renders."""
        from src.ui.pages.home import _render_metrics

        with (
            patch("src.ui.pages.home.ui.label"),
            patch("src.ui.pages.home.ui.column"),
            patch("src.ui.pages.home.ui.card"),
            patch("src.ui.pages.home.ui.row"),
            patch("src.ui.pages.home.ui.table") as mock_table,
            patch("src.ui.pages.home.ui.icon"),
        ):
            _render_metrics(
                claim_repo.get_all(), payment_repo.get_all(), period_repo.get_n_last(1)
            )

        # No table rendered (0 claims)
        mock_table.assert_not_called()


# ═══════════════════════════════════════════════════════════════════════════════
# Task 4.3 — Placeholder pages
# ═══════════════════════════════════════════════════════════════════════════════


class TestPlaceholderPages:
    """Verify each placeholder page registers correctly via its register function."""

    @pytest.mark.parametrize(
        "register_fn,route",
        [
            pytest.param(
                lambda: __import__(
                    "src.ui.pages.gestiones", fromlist=["register_gestiones_page"]
                ).register_gestiones_page(),
                "/gestiones",
                id="gestiones",
            ),
            pytest.param(
                lambda: __import__(
                    "src.ui.pages.gestiones_detalle",
                    fromlist=["register_gestiones_detalle_page"],
                ).register_gestiones_detalle_page(),
                "/gestiones/{id}",
                id="gestiones_detalle",
            ),
            pytest.param(
                lambda: __import__(
                    "src.ui.pages.pagos", fromlist=["register_pagos_page"]
                ).register_pagos_page(),
                "/pagos",
                id="pagos",
            ),
            pytest.param(
                lambda: __import__(
                    "src.ui.pages.periodos", fromlist=["register_periodos_page"]
                ).register_periodos_page(),
                "/periodos",
                id="periodos",
            ),
            pytest.param(
                lambda: __import__(
                    "src.ui.pages.reportes", fromlist=["register_reportes_page"]
                ).register_reportes_page(),
                "/reportes",
                id="reportes",
            ),
        ],
    )
    def test_placeholder_registers(self, register_fn, route):
        """GIVEN the register function WHEN called THEN @ui.page registers the route without error."""
        # The @ui.page decorator registers the route; AppShell runs only when the page is visited.
        # This test verifies the registration itself does not raise.
        register_fn()  # Should not raise
