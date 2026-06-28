"""Tests for gestiones.py data preparation layer — Task 2.1 (Strict TDD RED phase)."""

import pytest
from datetime import datetime
from unittest.mock import MagicMock
from uuid import uuid4

from src.adapters.persistence.inmemory_claim_repository import InMemoryClaimRepository
from src.adapters.persistence.inmemory_claim_kind_repository import (
    InMemoryClaimKindRepository,
)
from src.adapters.persistence.inmemory_sos_claim_repository import (
    InMemorySosClaimRepository,
)
from src.adapters.persistence.inmemory_payment_repository import (
    InMemoryPaymentRepository,
)
from src.adapters.persistence.inmemory_ncpayment_repository import (
    InMemoryNcPaymentRepository,
)
from src.domain.models.entities import Claim, ClaimKind, SosClaim, Payment
from src.ui.pages.gestiones import _prepare_gestiones_data


@pytest.fixture
def mock_container():
    """Create a test container with in-memory repositories for testing."""
    # Create in-memory repositories
    claim_repo = InMemoryClaimRepository()
    claim_kind_repo = InMemoryClaimKindRepository()
    sos_claim_repo = InMemorySosClaimRepository()
    payment_repo = InMemoryPaymentRepository()
    nc_payment_repo = InMemoryNcPaymentRepository()
    
    # Create a simple container object (not MagicMock to avoid pytest issues)
    class TestContainer:
        pass
    
    container = TestContainer()
    container.claim_repo = claim_repo
    container.claim_kind_repo = claim_kind_repo
    container.sos_claim_repo = sos_claim_repo
    container.payment_repo = payment_repo
    
    # Mock obtener_ncs use case to work with in-memory NC payment repo
    class MockObtenerNCs:
        def __init__(self, nc_payment_repo):
            self.nc_payment_repo = nc_payment_repo
        
        def get_by_payment_id(self, payment_id):
            all_ncs = self.nc_payment_repo.get_all()
            for nc in all_ncs:
                if nc.payment_id == payment_id:
                    return nc
            return None
    
    container.obtener_ncs = MockObtenerNCs(nc_payment_repo)
    
    return container


class TestPrepareGestionesData:
    """RED phase: Write failing tests for data prep function."""

    def test_prepare_empty_list_returns_empty(self, mock_container):
        """Given no claims, return empty list."""
        # Arrange: container with no claims (default state)
        # Act
        result = _prepare_gestiones_data(mock_container)
        # Assert
        assert result == []

    def test_prepare_single_claim_all_fields_populated(self, mock_container):
        """Given one claim, return one row with all fields populated."""
        # Arrange
        claim_id = uuid4()
        kind_id = uuid4()
        kind = ClaimKind(claim_kind_id=kind_id, name="Responsabilidad Civil")
        claim = Claim(
            claim_id=claim_id,
            claim_kind_id=kind_id,
            claimer_name="John Doe",
            policy_number="POL-123",
            plate="ABC123",
            claimed_amount=5000.00,
            created_at=datetime(2024, 1, 15),
            solved=False,
            active=True,
            group_id=None,
        )
        sos = SosClaim(gestion=123, claim_id=claim_id)
        
        mock_container.claim_repo.add(claim)
        mock_container.claim_kind_repo.add(kind)
        mock_container.sos_claim_repo.add(sos)
        
        # Act
        result = _prepare_gestiones_data(mock_container)
        
        # Assert
        assert len(result) == 1
        row = result[0]
        assert row['id'] == str(claim_id)
        assert row['claim_id'] == claim_id
        assert row['tipo'] == "Responsabilidad Civil"
        assert row['gestion'] == 123
        assert row['asegurado'] == "John Doe"
        assert row['poliza'] == "POL-123"
        assert row['patente'] == "ABC123"
        assert row['monto'] == "5,000.00"
        assert row['fecha'] == "15/01/2024"
        assert row['resuelto'] == "—"
        assert row['active'] == True
        assert row['has_group'] == False
        assert row['has_nc'] == False
        assert row['solved'] == False

    def test_prepare_solved_claim_shows_checkmark(self, mock_container):
        """Given solved claim, show ✓ in resuelto column."""
        # Arrange
        claim_id = uuid4()
        kind_id = uuid4()
        kind = ClaimKind(claim_kind_id=kind_id, name="Responsabilidad Civil")
        claim = Claim(
            claim_id=claim_id,
            claim_kind_id=kind_id,
            claimer_name="John Doe",
            policy_number="POL-123",
            plate="ABC123",
            claimed_amount=5000.00,
            created_at=datetime(2024, 1, 15),
            solved=True,  # <-- CHANGED
            active=True,
            group_id=None,
        )
        sos = SosClaim(gestion=123, claim_id=claim_id)
        
        mock_container.claim_repo.add(claim)
        mock_container.claim_kind_repo.add(kind)
        mock_container.sos_claim_repo.add(sos)
        
        # Act
        result = _prepare_gestiones_data(mock_container)
        
        # Assert
        assert result[0]['resuelto'] == "✓"
        assert result[0]['solved'] == True

    def test_prepare_claim_with_group_has_group_true(self, mock_container):
        """Given claim with group_id, has_group=True."""
        # Arrange
        group_id = uuid4()
        claim_id = uuid4()
        kind_id = uuid4()
        kind = ClaimKind(claim_kind_id=kind_id, name="Responsabilidad Civil")
        claim = Claim(
            claim_id=claim_id,
            claim_kind_id=kind_id,
            claimer_name="John Doe",
            policy_number="POL-123",
            plate="ABC123",
            claimed_amount=5000.00,
            created_at=datetime(2024, 1, 15),
            solved=False,
            active=True,
            group_id=group_id,  # <-- SET
        )
        sos = SosClaim(gestion=123, claim_id=claim_id)
        
        mock_container.claim_repo.add(claim)
        mock_container.claim_kind_repo.add(kind)
        mock_container.sos_claim_repo.add(sos)
        
        # Act
        result = _prepare_gestiones_data(mock_container)
        
        # Assert
        assert len(result) == 1
        assert result[0]['has_group'] == True

    def test_prepare_claim_with_nc_has_nc_true(self, mock_container):
        """Given claim with linked NC via payment, has_nc=True."""
        # Arrange
        from src.domain.models.entities import CreditNote
        
        claim_id = uuid4()
        kind_id = uuid4()
        payment_id = uuid4()
        nc_id = uuid4()
        
        kind = ClaimKind(claim_kind_id=kind_id, name="Responsabilidad Civil")
        claim = Claim(
            claim_id=claim_id,
            claim_kind_id=kind_id,
            claimer_name="John Doe",
            policy_number="POL-123",
            plate="ABC123",
            claimed_amount=5000.00,
            created_at=datetime(2024, 1, 15),
            solved=False,
            active=True,
            group_id=None,
        )
        sos = SosClaim(gestion=123, claim_id=claim_id)
        payment = Payment(
            payment_id=payment_id,
            claim_id=claim_id,
            amount=500.00,
            payment_method="Transferencia",
            payment_date=datetime(2024, 1, 16),
            automatic=False,
        )
        nc = CreditNote(
            nc_payment_id=nc_id,
            payment_id=payment_id,
            period_id=None,
            delivered=False,
        )
        
        mock_container.claim_repo.add(claim)
        mock_container.claim_kind_repo.add(kind)
        mock_container.sos_claim_repo.add(sos)
        mock_container.payment_repo.add(payment)
        # Access the nc_payment_repo through the obtener_ncs.nc_payment_repo
        mock_container.obtener_ncs.nc_payment_repo.add(nc)
        
        # Act
        result = _prepare_gestiones_data(mock_container)
        
        # Assert
        assert len(result) == 1
        assert result[0]['has_nc'] == True

    def test_prepare_inactive_claim_active_false(self, mock_container):
        """Given inactive claim, active=False."""
        # Arrange
        claim_id = uuid4()
        kind_id = uuid4()
        kind = ClaimKind(claim_kind_id=kind_id, name="Responsabilidad Civil")
        claim = Claim(
            claim_id=claim_id,
            claim_kind_id=kind_id,
            claimer_name="John Doe",
            policy_number="POL-123",
            plate="ABC123",
            claimed_amount=5000.00,
            created_at=datetime(2024, 1, 15),
            solved=False,
            active=False,  # <-- INACTIVE
            group_id=None,
        )
        sos = SosClaim(gestion=123, claim_id=claim_id)
        
        mock_container.claim_repo.add(claim)
        mock_container.claim_kind_repo.add(kind)
        mock_container.sos_claim_repo.add(sos)
        
        # Act
        result = _prepare_gestiones_data(mock_container)
        
        # Assert
        assert len(result) == 1
        assert result[0]['active'] == False

    def test_prepare_payment_count_per_claim(self, mock_container):
        """Given claim with N payments, cant_pagos=N."""
        # Arrange
        claim_id = uuid4()
        kind_id = uuid4()
        
        kind = ClaimKind(claim_kind_id=kind_id, name="Responsabilidad Civil")
        claim = Claim(
            claim_id=claim_id,
            claim_kind_id=kind_id,
            claimer_name="John Doe",
            policy_number="POL-123",
            plate="ABC123",
            claimed_amount=5000.00,
            created_at=datetime(2024, 1, 15),
            solved=False,
            active=True,
            group_id=None,
        )
        sos = SosClaim(gestion=123, claim_id=claim_id)
        
        # Create 3 payments for this claim
        for i in range(3):
            payment = Payment(
                payment_id=uuid4(),
                claim_id=claim_id,
                amount=1000.00 + i * 100,
                payment_method="Transferencia",
                payment_date=datetime(2024, 1, 16 + i),
                automatic=False,
            )
            mock_container.payment_repo.add(payment)
        
        mock_container.claim_repo.add(claim)
        mock_container.claim_kind_repo.add(kind)
        mock_container.sos_claim_repo.add(sos)
        
        # Act
        result = _prepare_gestiones_data(mock_container)
        
        # Assert
        assert len(result) == 1
        assert result[0]['cant_pagos'] == 3

    def test_prepare_multiple_claims_with_mixed_states(self, mock_container):
        """Given 3 claims with different states, return all 3 rows with correct data."""
        # Arrange
        kind_id = uuid4()
        kind = ClaimKind(claim_kind_id=kind_id, name="RC")
        
        # Claim 1: active, solved, with payments
        claim1_id = uuid4()
        claim1 = Claim(
            claim_id=claim1_id,
            claim_kind_id=kind_id,
            claimer_name="Alice",
            policy_number="POL-001",
            plate="AAA001",
            claimed_amount=1000.00,
            created_at=datetime(2024, 1, 1),
            solved=True,
            active=True,
            group_id=None,
        )
        sos1 = SosClaim(gestion=100, claim_id=claim1_id)
        pay1_1 = Payment(
            payment_id=uuid4(),
            claim_id=claim1_id,
            amount=500.00,
            payment_method="Transferencia",
            payment_date=datetime(2024, 1, 2),
            automatic=False,
        )
        
        # Claim 2: inactive, unsolved, no payments
        claim2_id = uuid4()
        claim2 = Claim(
            claim_id=claim2_id,
            claim_kind_id=kind_id,
            claimer_name="Bob",
            policy_number="POL-002",
            plate="BBB002",
            claimed_amount=2000.00,
            created_at=datetime(2024, 1, 5),
            solved=False,
            active=False,
            group_id=None,
        )
        sos2 = SosClaim(gestion=101, claim_id=claim2_id)
        
        # Claim 3: active, unsolved, with 2 payments
        claim3_id = uuid4()
        claim3 = Claim(
            claim_id=claim3_id,
            claim_kind_id=kind_id,
            claimer_name="Charlie",
            policy_number="POL-003",
            plate="CCC003",
            claimed_amount=3000.00,
            created_at=datetime(2024, 1, 10),
            solved=False,
            active=True,
            group_id=None,
        )
        sos3 = SosClaim(gestion=102, claim_id=claim3_id)
        pay3_1 = Payment(
            payment_id=uuid4(),
            claim_id=claim3_id,
            amount=1000.00,
            payment_method="Efectivo",
            payment_date=datetime(2024, 1, 11),
            automatic=False,
        )
        pay3_2 = Payment(
            payment_id=uuid4(),
            claim_id=claim3_id,
            amount=1000.00,
            payment_method="Cheque",
            payment_date=datetime(2024, 1, 12),
            automatic=False,
        )
        
        mock_container.claim_kind_repo.add(kind)
        mock_container.claim_repo.add(claim1)
        mock_container.claim_repo.add(claim2)
        mock_container.claim_repo.add(claim3)
        mock_container.sos_claim_repo.add(sos1)
        mock_container.sos_claim_repo.add(sos2)
        mock_container.sos_claim_repo.add(sos3)
        mock_container.payment_repo.add(pay1_1)
        mock_container.payment_repo.add(pay3_1)
        mock_container.payment_repo.add(pay3_2)
        
        # Act
        result = _prepare_gestiones_data(mock_container)
        
        # Assert
        assert len(result) == 3
        
        # Check claim 1
        r1 = next(r for r in result if r['asegurado'] == "Alice")
        assert r1['resuelto'] == "✓"
        assert r1['solved'] == True
        assert r1['active'] == True
        assert r1['cant_pagos'] == 1
        
        # Check claim 2
        r2 = next(r for r in result if r['asegurado'] == "Bob")
        assert r2['resuelto'] == "—"
        assert r2['solved'] == False
        assert r2['active'] == False
        assert r2['cant_pagos'] == 0
        
        # Check claim 3
        r3 = next(r for r in result if r['asegurado'] == "Charlie")
        assert r3['resuelto'] == "—"
        assert r3['solved'] == False
        assert r3['active'] == True
        assert r3['cant_pagos'] == 2
