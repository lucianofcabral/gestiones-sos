"""Tests for gestiones.py table rendering with ui.table (Tasks 2.2-2.7)."""

import pytest
from uuid import UUID
from unittest.mock import MagicMock

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


@pytest.fixture
def mock_container():
    """Create a test container with in-memory repositories for testing."""
    # Create in-memory repositories
    claim_repo = InMemoryClaimRepository()
    claim_kind_repo = InMemoryClaimKindRepository()
    sos_claim_repo = InMemorySosClaimRepository()
    payment_repo = InMemoryPaymentRepository()
    nc_payment_repo = InMemoryNcPaymentRepository()
    
    # Create a simple container object
    class TestContainer:
        pass
    
    container = TestContainer()
    container.claim_repo = claim_repo
    container.claim_kind_repo = claim_kind_repo
    container.sos_claim_repo = sos_claim_repo
    container.payment_repo = payment_repo
    
    # Mock obtener_ncs use case
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


class TestGestionesTableColumns:
    """RED phase: Test column definitions (Task 2.2)."""
    
    def test_gestiones_columns_defined(self):
        """All 10 columns defined with correct properties."""
        from src.ui.pages.gestiones import GESTIONES_COLUMNS
        
        assert len(GESTIONES_COLUMNS) == 10
        
        # Check column names in order
        names = [col['name'] for col in GESTIONES_COLUMNS]
        assert names == [
            'tipo', 'gestion', 'asegurado', 'poliza', 'patente',
            'monto', 'fecha', 'resuelto', 'cant_pagos', 'acciones'
        ]
    
    def test_gestiones_columns_have_required_properties(self):
        """Each column has required properties."""
        from src.ui.pages.gestiones import GESTIONES_COLUMNS
        
        for col in GESTIONES_COLUMNS:
            assert 'name' in col, f"Column {col.get('name', '?')} missing 'name'"
            assert 'label' in col, f"Column {col.get('name', '?')} missing 'label'"
            assert 'field' in col, f"Column {col.get('name', '?')} missing 'field'"
            assert 'align' in col, f"Column {col.get('name', '?')} missing 'align'"
            assert col['align'] in ['left', 'center', 'right'], \
                f"Column {col['name']} has invalid align: {col['align']}"
    
    def test_gestiones_columns_sortable_except_actions(self):
        """All columns sortable except 'acciones'."""
        from src.ui.pages.gestiones import GESTIONES_COLUMNS
        
        for col in GESTIONES_COLUMNS:
            if col['name'] == 'acciones':
                assert col.get('sortable', False) is False, \
                    "Actions column must not be sortable"
            else:
                assert col.get('sortable', True) is True, \
                    f"Column {col['name']} must be sortable"
    
    def test_monto_column_right_aligned(self):
        """Monto column must be right-aligned for numbers."""
        from src.ui.pages.gestiones import GESTIONES_COLUMNS
        
        monto_col = next((c for c in GESTIONES_COLUMNS if c['name'] == 'monto'), None)
        assert monto_col is not None, "Monto column not found"
        assert monto_col['align'] == 'right', \
            f"Monto column should be right-aligned, got {monto_col['align']}"
    
    def test_gestiones_columns_have_style_property(self):
        """Each column has a style property for min-width."""
        from src.ui.pages.gestiones import GESTIONES_COLUMNS
        
        for col in GESTIONES_COLUMNS:
            assert 'style' in col, \
                f"Column {col['name']} missing 'style' (min-width)"
            assert 'min-width' in col['style'], \
                f"Column {col['name']} style missing 'min-width'"


class TestGestionesActionsRender:
    """Test action icon rendering (Task 2.3)."""
    
    def test_render_gestiones_actions_function_exists(self):
        """_render_gestiones_actions function is defined."""
        from src.ui.pages.gestiones import _render_gestiones_actions
        
        assert callable(_render_gestiones_actions), \
            "_render_gestiones_actions must be a callable function"
    
    def test_render_gestiones_actions_accepts_claim_id_and_row_data(self):
        """Function has correct signature."""
        from src.ui.pages.gestiones import _render_gestiones_actions
        import inspect
        
        sig = inspect.signature(_render_gestiones_actions)
        params = list(sig.parameters.keys())
        
        # Must accept claim_id and row_data parameters
        assert 'claim_id' in params, "Function must have claim_id parameter"
        assert 'row_data' in params, "Function must have row_data parameter"


class TestGestionesTableDataIntegration:
    """Test data preparation and filtering (Tasks 2.4-2.7)."""
    
    def test_prepare_gestiones_data_returns_correct_structure(self, mock_container):
        """_prepare_gestiones_data returns dicts with all required fields."""
        from src.ui.pages.gestiones import _prepare_gestiones_data
        
        data = _prepare_gestiones_data(mock_container)
        
        # Can be empty if no claims
        if data:
            row = data[0]
            required_fields = [
                'id', 'claim_id', 'tipo', 'gestion', 'asegurado', 'poliza',
                'patente', 'monto', 'fecha', 'resuelto', 'cant_pagos',
                'active', 'has_group', 'has_nc', 'solved'
            ]
            for field in required_fields:
                assert field in row, f"Row missing field: {field}"
    
    def test_gestiones_columns_match_prepared_data_fields(self, mock_container):
        """Column names match fields in prepared data."""
        from src.ui.pages.gestiones import GESTIONES_COLUMNS, _prepare_gestiones_data
        
        data = _prepare_gestiones_data(mock_container)
        
        # Get field names from columns
        column_fields = {col['field'] for col in GESTIONES_COLUMNS 
                        if col['name'] != 'acciones'}
        
        # Verify prepared data can provide these fields
        if data:
            row = data[0]
            for field in column_fields:
                assert field in row, \
                    f"Prepared data missing field '{field}' from GESTIONES_COLUMNS"
    
    def test_filtering_by_active_status(self, mock_container):
        """Data can be filtered by active/inactive status."""
        from src.ui.pages.gestiones import _prepare_gestiones_data
        from src.domain.models.entities import Claim, ClaimKind
        from uuid import uuid4
        from datetime import datetime
        
        # Add test claim
        kind = ClaimKind(claim_kind_id=uuid4(), name='SOS')
        mock_container.claim_kind_repo.add(kind)
        
        claim_id = uuid4()
        claim = Claim(
            claim_id=claim_id,
            claimer_name='John Doe',
            policy_number='POL123',
            plate='ABC1234',
            claimed_amount=1000.00,
            claim_kind_id=kind.claim_kind_id,
            created_at=datetime.now(),
            active=False  # Inactive claim
        )
        mock_container.claim_repo.add(claim)
        
        data = _prepare_gestiones_data(mock_container)
        assert len(data) == 1
        assert data[0]['active'] is False
    
    def test_data_includes_solved_status(self, mock_container):
        """Prepared data includes solved status."""
        from src.ui.pages.gestiones import _prepare_gestiones_data
        from src.domain.models.entities import Claim, ClaimKind
        from uuid import uuid4
        from datetime import datetime
        
        kind = ClaimKind(claim_kind_id=uuid4(), name='SOS')
        mock_container.claim_kind_repo.add(kind)
        
        claim = Claim(
            claim_id=uuid4(),
            claimer_name='Test',
            policy_number='POL123',
            plate='ABC1234',
            claimed_amount=100.0,
            claim_kind_id=kind.claim_kind_id,
            created_at=datetime.now(),
            solved=True
        )
        mock_container.claim_repo.add(claim)
        
        data = _prepare_gestiones_data(mock_container)
        assert len(data) == 1
        assert data[0]['solved'] is True
        assert data[0]['resuelto'] == '✓'


class TestGestionesSortingFunction:
    """Test sorting behavior for _sort_prepared_data (Task 2.4 - Sorting)."""
    
    def test_sort_by_monto_descending(self):
        """Given multiple rows, sort by monto descending works correctly."""
        from src.ui.pages.gestiones import _sort_prepared_data
        
        # Create test rows with different montos
        rows = [
            {'monto': '1,000.00', 'tipo': 'SOS'},
            {'monto': '500.00', 'tipo': 'SOS'},
            {'monto': '2,500.00', 'tipo': 'SOS'},
        ]
        
        # Sort by monto (column index 5) descending (direction -1)
        sorted_rows = _sort_prepared_data(rows, sort_col=5, sort_dir=-1)
        
        # Extract montos as floats for comparison
        montos = [float(r['monto'].replace(',', '')) for r in sorted_rows]
        assert montos == [2500.00, 1000.00, 500.00]
    
    def test_sort_by_asegurado_ascending(self):
        """Given multiple rows, sort by asegurado ascending works correctly."""
        from src.ui.pages.gestiones import _sort_prepared_data
        
        rows = [
            {'asegurado': 'Zara Limited'},
            {'asegurado': 'Alice Corp'},
            {'asegurado': 'Bob Inc'},
        ]
        
        # Sort by asegurado (column index 2) ascending (direction 1)
        sorted_rows = _sort_prepared_data(rows, sort_col=2, sort_dir=1)
        
        names = [r['asegurado'] for r in sorted_rows]
        assert names == ['Alice Corp', 'Bob Inc', 'Zara Limited']
    
    def test_sort_acciones_column_returns_unchanged(self):
        """Actions column (index 9) is not sortable; rows unchanged."""
        from src.ui.pages.gestiones import _sort_prepared_data
        
        rows = [
            {'asegurado': 'Zara', 'acciones': 'edit'},
            {'asegurado': 'Alice', 'acciones': 'edit'},
        ]
        original_order = [r['asegurado'] for r in rows]
        
        # Try to sort by acciones (column 9)
        sorted_rows = _sort_prepared_data(rows, sort_col=9, sort_dir=1)
        
        # Should be unchanged (returns original order)
        result_order = [r['asegurado'] for r in sorted_rows]
        assert result_order == original_order


class TestGestionesFilteringFunction:
    """Test filtering behavior for _apply_filters_to_prepared_data (Task 2.5 - Filtering)."""
    
    def test_filter_active_only(self):
        """Given mixed active/inactive rows, filter_active=True returns only active."""
        from src.ui.pages.gestiones import _apply_filters_to_prepared_data
        
        rows = [
            {'active': True, 'tipo': 'SOS', 'gestion': '123', 'asegurado': 'A', 
             'poliza': '', 'patente': '', 'solved': False},
            {'active': False, 'tipo': 'SOS', 'gestion': '124', 'asegurado': 'B',
             'poliza': '', 'patente': '', 'solved': False},
        ]
        
        filtered = _apply_filters_to_prepared_data(
            rows,
            filter_kind=None,
            filter_text=None,
            filter_solved=False,
            filter_has_payments=False,
            filter_no_payments=False,
            filter_has_nc=False,
            filter_no_nc=False,
            show_inactive=False  # Only show active
        )
        
        assert len(filtered) == 1
        assert filtered[0]['active'] is True
    
    def test_filter_by_claim_kind(self):
        """Given kind filter, only matching kind rows returned."""
        from src.ui.pages.gestiones import _apply_filters_to_prepared_data
        
        rows = [
            {'tipo': 'SOS', 'active': True, 'gestion': '123', 'asegurado': 'A',
             'poliza': '', 'patente': '', 'solved': False},
            {'tipo': 'Grouped', 'active': True, 'gestion': '124', 'asegurado': 'B',
             'poliza': '', 'patente': '', 'solved': False},
        ]
        
        filtered = _apply_filters_to_prepared_data(
            rows,
            filter_kind='SOS',
            filter_text=None,
            filter_solved=False,
            filter_has_payments=False,
            filter_no_payments=False,
            filter_has_nc=False,
            filter_no_nc=False,
            show_inactive=True
        )
        
        assert len(filtered) == 1
        assert filtered[0]['tipo'] == 'SOS'
    
    def test_filter_by_text_search(self):
        """Given text filter, only rows with matching text returned."""
        from src.ui.pages.gestiones import _apply_filters_to_prepared_data
        
        rows = [
            {'asegurado': 'John Smith', 'poliza': 'POL-001', 'patente': 'ABC123',
             'gestion': '999', 'tipo': 'SOS', 'active': True, 'solved': False},
            {'asegurado': 'Jane Doe', 'poliza': 'POL-002', 'patente': 'XYZ789',
             'gestion': '888', 'tipo': 'SOS', 'active': True, 'solved': False},
        ]
        
        filtered = _apply_filters_to_prepared_data(
            rows,
            filter_kind=None,
            filter_text='John',
            filter_solved=False,
            filter_has_payments=False,
            filter_no_payments=False,
            filter_has_nc=False,
            filter_no_nc=False,
            show_inactive=True
        )
        
        assert len(filtered) == 1
        assert 'John' in filtered[0]['asegurado']
    
    def test_filter_by_solved_status(self):
        """Given solved filter, only solved rows returned."""
        from src.ui.pages.gestiones import _apply_filters_to_prepared_data
        
        rows = [
            {'solved': True, 'tipo': 'SOS', 'active': True, 'gestion': '123',
             'asegurado': 'A', 'poliza': '', 'patente': ''},
            {'solved': False, 'tipo': 'SOS', 'active': True, 'gestion': '124',
             'asegurado': 'B', 'poliza': '', 'patente': ''},
        ]
        
        filtered = _apply_filters_to_prepared_data(
            rows,
            filter_kind=None,
            filter_text=None,
            filter_solved=True,  # Only solved
            filter_has_payments=False,
            filter_no_payments=False,
            filter_has_nc=False,
            filter_no_nc=False,
            show_inactive=True
        )
        
        assert len(filtered) == 1
        assert filtered[0]['solved'] is True
    
    def test_filter_by_has_payments(self):
        """Given has_payments filter, only rows with payments returned."""
        from src.ui.pages.gestiones import _apply_filters_to_prepared_data
        
        rows = [
            {'cant_pagos': 1, 'tipo': 'SOS', 'active': True, 'gestion': '123',
             'asegurado': 'A', 'poliza': '', 'patente': '', 'solved': False},
            {'cant_pagos': 0, 'tipo': 'SOS', 'active': True, 'gestion': '124',
             'asegurado': 'B', 'poliza': '', 'patente': '', 'solved': False},
        ]
        
        filtered = _apply_filters_to_prepared_data(
            rows,
            filter_kind=None,
            filter_text=None,
            filter_solved=False,
            filter_has_payments=True,  # Only with payments
            filter_no_payments=False,
            filter_has_nc=False,
            filter_no_nc=False,
            show_inactive=True
        )
        
        assert len(filtered) == 1
        assert filtered[0]['cant_pagos'] > 0
    
    def test_filter_by_has_nc(self):
        """Given has_nc filter, only rows with NC returned."""
        from src.ui.pages.gestiones import _apply_filters_to_prepared_data
        
        rows = [
            {'has_nc': True, 'tipo': 'SOS', 'active': True, 'gestion': '123',
             'asegurado': 'A', 'poliza': '', 'patente': '', 'solved': False},
            {'has_nc': False, 'tipo': 'SOS', 'active': True, 'gestion': '124',
             'asegurado': 'B', 'poliza': '', 'patente': '', 'solved': False},
        ]
        
        filtered = _apply_filters_to_prepared_data(
            rows,
            filter_kind=None,
            filter_text=None,
            filter_solved=False,
            filter_has_payments=False,
            filter_no_payments=False,
            filter_has_nc=True,  # Only with NC
            filter_no_nc=False,
            show_inactive=True
        )
        
        assert len(filtered) == 1
        assert filtered[0]['has_nc'] is True
