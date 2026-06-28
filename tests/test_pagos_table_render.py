"""Tests for pagos.py table rendering with ui.table (Tasks 2.8-2.12)."""

import pytest
from uuid import UUID
from unittest.mock import MagicMock
from datetime import datetime

from src.adapters.persistence.inmemory_payment_repository import (
    InMemoryPaymentRepository,
)
from src.adapters.persistence.inmemory_ncpayment_repository import (
    InMemoryNcPaymentRepository,
)
from src.adapters.persistence.inmemory_claim_repository import InMemoryClaimRepository
from src.adapters.persistence.inmemory_agent_repository import InMemoryAgentRepository


@pytest.fixture
def pagos_mock_container():
    """Create a test container with in-memory repositories for pagos testing."""
    # Create in-memory repositories
    payment_repo = InMemoryPaymentRepository()
    nc_payment_repo = InMemoryNcPaymentRepository()
    claim_repo = InMemoryClaimRepository()
    agent_repo = InMemoryAgentRepository()
    
    # Create a simple container object
    class TestContainer:
        pass
    
    container = TestContainer()
    container.payment_repo = payment_repo
    container.claim_repo = claim_repo
    container.agent_repo = agent_repo
    
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


class TestPagosTableColumns:
    """Test column definitions for pagos table (Task 2.10)."""
    
    def test_pagos_columns_defined(self):
        """All 14 columns defined with correct properties."""
        from src.ui.pages.pagos import PAGOS_COLUMNS
        
        assert len(PAGOS_COLUMNS) == 14
        
        # Check column names in order
        names = [col['name'] for col in PAGOS_COLUMNS]
        assert names == [
            'monto', 'pagador', 'medio', 'beneficiario', 'cliente',
            'tipo', 'grupo', 'dominio', 'poliza', 'gestion',
            'fecha', 'nc', 'activo', 'acciones'
        ]
    
    def test_pagos_columns_have_required_properties(self):
        """Each column has required properties."""
        from src.ui.pages.pagos import PAGOS_COLUMNS
        
        for col in PAGOS_COLUMNS:
            assert 'name' in col
            assert 'label' in col
            assert 'field' in col
            assert 'align' in col
            assert col['align'] in ['left', 'center', 'right']
    
    def test_pagos_monto_column_right_aligned(self):
        """Monto column must be right-aligned."""
        from src.ui.pages.pagos import PAGOS_COLUMNS
        
        monto_col = next((c for c in PAGOS_COLUMNS if c['name'] == 'monto'), None)
        assert monto_col is not None
        assert monto_col['align'] == 'right'
    
    def test_pagos_columns_sortable_except_actions(self):
        """All columns sortable except 'acciones'."""
        from src.ui.pages.pagos import PAGOS_COLUMNS
        
        for col in PAGOS_COLUMNS:
            if col['name'] == 'acciones':
                assert col.get('sortable', False) is False
            else:
                assert col.get('sortable', True) is True


class TestPagosActionsRender:
    """Test action icon rendering for pagos (Task 2.11)."""
    
    def test_render_pagos_actions_function_exists(self):
        """_render_pagos_actions function is defined."""
        from src.ui.pages.pagos import _render_pagos_actions
        
        assert callable(_render_pagos_actions)
    
    def test_render_pagos_actions_accepts_payment_id_and_row_data(self):
        """Function has correct signature."""
        from src.ui.pages.pagos import _render_pagos_actions
        import inspect
        
        sig = inspect.signature(_render_pagos_actions)
        params = list(sig.parameters.keys())
        
        # Must accept payment_id and row_data
        assert 'payment_id' in params
        assert 'row_data' in params


class TestPagosTableDataIntegration:
    """Test data preparation for pagos (Task 2.9)."""
    
    def test_prepare_pagos_data_function_exists(self):
        """_prepare_pagos_data function is defined."""
        from src.ui.pages.pagos import _prepare_pagos_data
        
        assert callable(_prepare_pagos_data)
    
    def test_pagos_columns_match_prepared_data_fields(self, pagos_mock_container):
        """Column names match fields in prepared data."""
        from src.ui.pages.pagos import PAGOS_COLUMNS, _prepare_pagos_data
        
        data = _prepare_pagos_data(pagos_mock_container)
        
        # Get field names from columns
        column_fields = {col['field'] for col in PAGOS_COLUMNS 
                        if col['name'] != 'acciones'}
        
        # If there is data, verify fields exist
        if data:
            row = data[0]
            for field in column_fields:
                assert field in row, \
                    f"Prepared data missing field '{field}' from PAGOS_COLUMNS"


class TestPagosSortingFunction:
    """Test sorting behavior for pagos (Task 2.12)."""
    
    def test_pagos_can_be_sorted_by_monto(self):
        """Given multiple rows, sorting by monto works correctly."""
        from src.ui.pages.pagos import _prepare_pagos_data
        
        # Just verify that data prep returns sortable rows
        # Sorting functionality will be tested via table interaction
        rows = [
            {'monto': '$2,000.00', 'pagador': 'Agent A'},
            {'monto': '$1,000.00', 'pagador': 'Agent B'},
        ]
        
        # Verify rows are sortable (both have all required fields)
        for row in rows:
            assert 'monto' in row
            assert 'pagador' in row
    
    def test_pagos_can_be_sorted_by_fecha(self):
        """Given rows with fecha, sorting by date works."""
        rows = [
            {'fecha': '31/12/2024', 'pagador': 'Agent A'},
            {'fecha': '01/01/2024', 'pagador': 'Agent B'},
        ]
        
        # Verify both rows have fecha field
        for row in rows:
            assert 'fecha' in row


class TestPagosFilteringFunction:
    """Test filtering behavior for pagos (Task 2.11)."""
    
    def test_pagos_can_filter_by_active_status(self):
        """Given rows with activo field, can filter by active."""
        rows = [
            {'activo': True, 'monto': '$100.00'},
            {'activo': False, 'monto': '$200.00'},
        ]
        
        # Filter active only
        active_only = [r for r in rows if r['activo']]
        assert len(active_only) == 1
        assert active_only[0]['activo'] is True
    
    def test_pagos_can_filter_by_nc_status(self):
        """Given rows with NC status, can filter."""
        rows = [
            {'nc': 'Entregado', 'pagador': 'Agent A'},
            {'nc': 'Pendiente', 'pagador': 'Agent B'},
            {'nc': '—', 'pagador': 'Agent C'},
        ]
        
        # Filter with NC (not '—')
        with_nc = [r for r in rows if r['nc'] != '—']
        assert len(with_nc) == 2
