# Design: Billing CRUD — Invoices

## Technical Approach

Mirror the GroupClaim pattern end-to-end. New `invoices` table, `SqlAlchemyBillingRepository`, `InMemoryBillingRepository`, five use cases, and a UI page at `/facturas`. `get_total_billing_by_year_month` queries `invoices` via JOIN in the SQLAlchemy period repo and receives an invoice store reference in the in-memory one. Migration targets `3a8f9c1e4b6d` (current head).

## Data Flow

```
/facturas (UI) ──→ RegistrarFactura     ──→ BillingRepoPort.add()
                  → ObtenerFacturas      ──→ repo.get_all() / get_by_period_id()
                  → ObtenerFactura       ──→ repo.get_by_id()
                  → EliminarFactura      ──→ DocumentRepoPort.get_by_billing_id() check → repo.delete(id)
                  → ObtenerTotalFacturacion─→ PeriodRepoPort.get_total_billing_by_year_month()

CanInactivatePaymentService ──→ BillingRepoPort.get_by_period_id()  (replaces stub)
```

## Architecture Decisions

| Option | Tradeoffs | Decision |
|--------|-----------|----------|
| `invoice_number` type | int auto-increment vs str from SOS | **str** — external code, user-entered |
| Delete integrity | DB-level CASCADE vs app-level check | **App-level** via `DocumentRepoPort.get_by_billing_id()`, consistent with GroupClaim pattern |
| `get_total_billing` impl | New port on BillingRepo vs existing PeriodRepo | **Existing PeriodRepo** — port already defined, just replace `NotImplementedError` |
| In-memory period repo access | Own invoice store vs accept billing repo ref | **Accept `list[Invoice]`** — follows `InMemoryGroupClaimRepository(claim_store)` pattern |

## Domain Changes

```python
# src/domain/models/entities.py
class Invoice(BaseModel):
    invoice_id: UUID = Field(default_factory=uuid4)
    invoice_number: str      # int → str
    period_id: UUID
    emited_date: datetime
    amount: float = Field(gt=0)
    created_at: datetime = Field(default_factory=datetime.now)
```

## File Changes

| File | Action | Description |
|------|--------|-------------|
| `src/domain/models/entities.py` | Modify | `invoice_number: int` → `str` |
| `src/infrastructure/database/tables.py` | Modify | Add `invoices` table def |
| `alembic/versions/xxxxxxxxxxxx_create_invoices_table.py` | New | Migration: `down_revision="3a8f9c1e4b6d"`, create `invoices` |
| `src/adapters/persistence/sqlalchemy_billing_repository.py` | New | `SqlAlchemyBillingRepository` — `BaseRepo` + `_DocReachable` stubs + `get_by_period_id` |
| `src/adapters/persistence/inmemory_billing_repository.py` | New | `InMemoryBillingRepository` for tests |
| `src/application/use_cases/billing/registrar_factura.py` | New | Input: invoice fields; output: Invoice |
| `src/application/use_cases/billing/obtener_facturas.py` | New | List all or by period |
| `src/application/use_cases/billing/obtener_factura.py` | New | Get by ID |
| `src/application/use_cases/billing/eliminar_factura.py` | New | Delete with document integrity check |
| `src/application/use_cases/billing/obtener_total_facturacion.py` | New | Total billing by year/month |
| `src/infrastructure/container.py` | Modify | Replace `_StubBillingRepository` with `SqlAlchemyBillingRepository`, wire use cases |
| `src/adapters/persistence/sqlalchemy_period_repository.py` | Modify | Implement `get_total_billing_by_year_month` — JOIN invoices |
| `src/adapters/persistence/inmemory_period_repository.py` | Modify | Implement `get_total_billing_by_year_month` — filter invoice store |
| `src/ui/pages/facturacion.py` | New | List by period + create form at `/facturas` |
| `src/ui/components/shell.py` | Modify | Add `("Facturación", "/facturas", "receipt")` to nav |
| `main.py` | Modify | Import + call `register_facturacion_page()` |
| `tests/test_billing.py` | New | In-memory repo + use case tests |

## Interfaces / Contracts

### `invoices` table

```python
invoices = sa.Table(
    "invoices", metadata,
    sa.Column("invoice_id", sa.UUID, primary_key=True),
    sa.Column("invoice_number", sa.String(50), nullable=False),
    sa.Column("period_id", sa.UUID, sa.ForeignKey("periods.period_id"), nullable=False),
    sa.Column("emited_date", sa.DateTime, nullable=False),
    sa.Column("amount", sa.Numeric(12, 2), nullable=False),
    sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
)
```

### Key repo methods

```python
# SqlAlchemyBillingRepository.get_by_period_id
def get_by_period_id(self, period_id: UUID) -> list[Invoice]:
    with self._get_conn() as conn:
        rows = conn.execute(
            sa.select(invoices).where(invoices.c.period_id == period_id)
        ).fetchall()
    return [self._row_to_entity(r) for r in rows]

# SqlAlchemyPeriodRepository.get_total_billing_by_year_month
from src.infrastructure.database.tables import invoices as inv_tbl

def get_total_billing_by_year_month(self, year: int, month: int) -> float:
    with self._get_conn() as conn:
        row = conn.execute(
            sa.select(sa.func.coalesce(sa.func.sum(inv_tbl.c.amount), 0))
            .select_from(periods.join(inv_tbl, periods.c.period_id == inv_tbl.c.period_id))
            .where(sa.and_(periods.c.year == year, periods.c.month == month))
        ).scalar()
    return float(row)
```

### `EliminarFactura` — integrity check

```python
class EliminarFactura:
    def __init__(self, billing_repo: BillingRepoPort, document_repo: DocumentRepoPort): ...
    def execute(self, invoice_id: UUID) -> bool:
        invoice = self._billing_repo.get_by_id(invoice_id)
        if invoice is None: return False
        if self._document_repo.get_by_billing_id(invoice_id) is not None:
            raise ValueError("No se puede eliminar: la factura tiene documentos asociados")
        self._billing_repo.delete(invoice_id)
        return True
```

## Testing Strategy

| Layer | What to Test | Approach |
|-------|-------------|----------|
| In-memory repo | BaseRepo methods + `get_by_period_id` + `_DocReachable` stubs | Seed data, assert CRUD + filtering |
| Use cases | RegistrarFactura, ObtenerFacturas, ObtenerFactura, EliminarFactura, ObtenerTotalFacturacion | In-memory repos as injected deps |
| Period repo billing | `get_total_billing_by_year_month` in both impls | SQLAlchemy uses test DB; in-memory uses shared invoice store |
| UI | Page renders + create flow | Manual (NiceGUI) |

## Migration / Rollout

`alembic upgrade head` creates `invoices` table (FK→periods). Rollback: `alembic downgrade -1`. No data migration — no production invoices exist. Revert files in reverse order, re-enable `_StubBillingRepository`.
