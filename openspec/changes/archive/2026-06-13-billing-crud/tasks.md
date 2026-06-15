# Tasks: Billing CRUD — Invoices

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | ~760–810 |
| 400-line budget risk | High |
| Review budget (custom) | 800 lines |
| Chained PRs recommended | No |
| Suggested split | Single PR |
| Delivery strategy | auto-forecast |
| Chain strategy | size-exception |

Decision needed before apply: No
Chained PRs recommended: No
Chain strategy: size-exception
400-line budget risk: High

### Suggested Work Units

| Unit | Goal | Likely PR | Notes |
|------|------|-----------|-------|
| 1 | Full Billing CRUD stack — domain → schema → repos → use cases → container → UI → tests | PR 1 | Single PR, same pattern as group-claim (size-exception precedent) |

## Phase 1: Domain Changes

- [x] 1.1 Change `Invoice.invoice_number` from `int` to `str` in `src/domain/models/entities.py`
  - `invoice_number: int = Field(0, ge=0)` → `invoice_number: str`
  - Remove `ge=0` validation, let it be a non-empty string validated by SOS input
  - **Files:** `src/domain/models/entities.py`
  - **Dependencies:** None

## Phase 2: DB Schema

- [x] 2.1 Add `invoices` table definition to `src/infrastructure/database/tables.py`
  - Mirror entity fields: `invoice_id` (UUID PK), `invoice_number` (String(50), non-null), `period_id` (UUID, FK → periods.period_id), `emited_date` (DateTime), `amount` (Numeric(12,2)), `created_at` (DateTime, server_default now())
  - Import `sqlalchemy as sa`, add to existing `metadata`
  - **Files:** `src/infrastructure/database/tables.py`
  - **Dependencies:** None

- [x] 2.2 Create Alembic migration: `alembic/versions/xxxxxxxxxxxx_create_invoices_table.py`
  - `down_revision = "3a8f9c1e4b6d"` (current head)
  - `upgrade()`: `op.create_table("invoices", ...)` with all columns + FK
  - `downgrade()`: `op.drop_table("invoices")`
  - **Files:** `alembic/versions/xxxxxxxxxxxx_create_invoices_table.py`
  - **Dependencies:** 2.1 (table def should be in metadata first for consistency, though migration is manual)

## Phase 3: Repositories

- [x] 3.1 Create `src/adapters/persistence/sqlalchemy_billing_repository.py`
  - `SqlAlchemyBillingRepository` — follows exact `SqlAlchemyGroupClaimRepository` pattern
  - `_get_conn()` context manager for connection lifecycle
  - `_row_to_entity(row)` → `Invoice(...)` mapper
  - BaseRepo methods: `add`, `get_by_id`, `delete`, `update`, `get_all`, `exists`, `get_by_ids`
  - BillingRepoPort method: `get_by_period_id(period_id)` — `sa.select(invoices).where(invoices.c.period_id == period_id)`
  - `_DocReachable` stubs: `get_by_document_id`, `get_by_document` both return `[]`
  - **Files:** `src/adapters/persistence/sqlalchemy_billing_repository.py`
  - **Dependencies:** 2.1 (invoices table)

- [x] 3.2 Create `src/adapters/persistence/inmemory_billing_repository.py`
  - `InMemoryBillingRepository` — follows exact `InMemoryGroupClaimRepository` pattern
  - `_store: list[Invoice]` in-memory
  - BaseRepo methods: `add`, `get_by_id`, `delete`, `update`, `get_all`, `exists`, `get_by_ids`
  - BillingRepoPort method: `get_by_period_id(period_id)` — filter by `period_id`
  - `_DocReachable` stubs: `get_by_document_id`, `get_by_document` both return `[]`
  - **Files:** `src/adapters/persistence/inmemory_billing_repository.py`
  - **Dependencies:** 1.1 (Invoice entity)

## Phase 4: Period Repository — Total Billing

- [x] 4.1 Implement `SqlAlchemyPeriodRepository.get_total_billing_by_year_month`
  - Replace `raise NotImplementedError(...)` with real query:
    ```python
    sa.select(sa.func.coalesce(sa.func.sum(inv_tbl.c.amount), 0))
    .select_from(periods.join(inv_tbl, periods.c.period_id == inv_tbl.c.period_id))
    .where(sa.and_(periods.c.year == year, periods.c.month == month))
    ```
  - Import `invoices as inv_tbl` from `src.infrastructure.database.tables`
  - **Files:** `src/adapters/persistence/sqlalchemy_period_repository.py`
  - **Dependencies:** 2.1 (invoices table)

- [x] 4.2 Implement `InMemoryPeriodRepository.get_total_billing_by_year_month`
  - Replace `raise NotImplementedError(...)` with filter + sum logic
  - Receives `invoice_store: list[Invoice]` param via constructor
  - Filter invoices by period's year/month, sum amounts, return `float`
  - **Files:** `src/adapters/persistence/inmemory_period_repository.py`
  - **Dependencies:** 1.1 (Invoice entity)

## Phase 5: Use Cases

- [x] 5.1 Create `src/application/use_cases/billing/registrar_factura.py`
  - `RegistrarFactura` — input: `invoice_number`, `period_id`, `emited_date`, `amount`
  - Creates `Invoice` entity with auto-generated `invoice_id` and `created_at`
  - Calls `billing_repo.add(invoice)`, returns created Invoice
  - Validates inputs: non-empty invoice_number, amount > 0
  - **Files:** `src/application/use_cases/billing/registrar_factura.py`
  - **Dependencies:** 3.1 / 3.2 (BillingRepoPort)

- [x] 5.2 Create `src/application/use_cases/billing/obtener_facturas.py`
  - `ObtenerFacturas` — `execute()` returns all invoices
  - `por_periodo(period_id)` returns invoices filtered by period
  - **Files:** `src/application/use_cases/billing/obtener_facturas.py`
  - **Dependencies:** 3.1 / 3.2 (BillingRepoPort)

- [x] 5.3 Create `src/application/use_cases/billing/obtener_factura.py`
  - `ObtenerFactura` — `execute(invoice_id)` returns `Invoice | None`
  - **Files:** `src/application/use_cases/billing/obtener_factura.py`
  - **Dependencies:** 3.1 / 3.2 (BillingRepoPort)

- [x] 5.4 Create `src/application/use_cases/billing/eliminar_factura.py`
  - `EliminarFactura` — takes `billing_repo` + `document_repo`
  - `execute(invoice_id)`:
    1. Get invoice by ID — return `False` if None
    2. Check `document_repo.get_by_billing_id(invoice_id)` — if exists, raise `ValueError("No se puede eliminar: la factura tiene documentos asociados")`
    3. Delete invoice, return `True`
  - **Files:** `src/application/use_cases/billing/eliminar_factura.py`
  - **Dependencies:** 3.1 / 3.2 (BillingRepoPort), DocumentRepoPort

- [x] 5.5 Create `src/application/use_cases/billing/obtener_total_facturacion.py`
  - `ObtenerTotalFacturacion` — takes `period_repo`
  - `execute(year, month)` calls `period_repo.get_total_billing_by_year_month(year, month)`
  - Returns `float`
  - **Files:** `src/application/use_cases/billing/obtener_total_facturacion.py`
  - **Dependencies:** 4.1 / 4.2 (period repo billing queries)

## Phase 6: Container Wiring

- [x] 6.1 Replace `_StubBillingRepository` with real `SqlAlchemyBillingRepository` in `src/infrastructure/container.py`
  - Add `_build_billing_repo()` factory fn (follows `_build_group_claim_repo()` pattern)
  - Replace `self._billing_repo: BillingRepoPort = _StubBillingRepository()` with `self._billing_repo = _build_billing_repo()`
  - Import `SqlAlchemyBillingRepository`

- [x] 6.2 Wire 5 billing use cases as properties in container
  - `self._registrar_factura = RegistrarFactura(self._billing_repo)`
  - `self._obtener_facturas = ObtenerFacturas(self._billing_repo)`
  - `self._obtener_factura = ObtenerFactura(self._billing_repo)`
  - `self._eliminar_factura = EliminarFactura(self._billing_repo, self._document_repo)`
  - `self._obtener_total_facturacion = ObtenerTotalFacturacion(self._period_repo)`
  - Add `@property` accessors for all 5 use cases
  - Remove `_StubBillingRepository` class
  - **Files:** `src/infrastructure/container.py`
  - **Dependencies:** 5.1–5.5 (all use cases)

## Phase 7: UI Page

- [x] 7.1 Create `src/ui/pages/facturacion.py`
  - `@ui.page("/facturas")` with `register_facturacion_page()`
  - Uses `AppShell` for layout
  - Period selector (dropdown from `container.period_repo.get_n_last(12)`)
  - Invoice list (`ui.table`) — columns: invoice_number, emited_date, amount
  - Create form: `ui.input` for invoice_number, `ui.date` for date, `ui.number` for amount + `ui.button("Registrar")`
  - Delete buttons with document integrity error handling (`ui.notify`)
  - "Total facturado" label showing sum from `ObtenerTotalFacturacion`
  - Refresh table on period select / create / delete
  - **Files:** `src/ui/pages/facturacion.py`
  - **Dependencies:** 6.2 (container wired)

- [x] 7.2 Add `("Facturación", "/facturas", "receipt")` to `AppShell._nav_items()` in `src/ui/components/shell.py`
  - Insert between "Pagos" and "Períodos" or at end (follow existing order)
  - **Files:** `src/ui/components/shell.py`
  - **Dependencies:** None

- [x] 7.3 Register facturacion page in `main.py`
  - Add `from src.ui.pages.facturacion import register_facturacion_page`
  - Call `register_facturacion_page()` before `ui.run()`
  - **Files:** `main.py`
  - **Dependencies:** 7.1 (page exists)

## Phase 8: Tests

- [x] 8.1 Create `tests/test_billing.py`
  - Follow exact pattern from `tests/test_grupos.py`
  - **Fixtures:**
    - `billing_repo()` → `InMemoryBillingRepository()`
    - `period_repo_with_invoices(invoice_store)` → `InMemoryPeriodRepository(invoice_store=...)`
  - **Seed helpers:**
    - `_seed_invoice(repo, ...)` — create + add Invoice with defaults
    - `_seed_period(repo, ...)` — create + add Period with defaults
  - **InMemoryBillingRepository tests (class TestBillingRepo):**
    - BaseRepo: `get_by_id` (found / not found), `add`, `get_all` (multiple / empty), `exists`, `update`, `delete`, `get_by_ids`
    - BillingRepoPort: `get_by_period_id` (returns filtered / empty)
    - `_DocReachable` stubs: `get_by_document_id`, `get_by_document`
  - **Use case tests:**
    - `TestRegistrarFactura` — creates invoice, validates inputs
    - `TestObtenerFacturas` — all, by period, empty
    - `TestObtenerFactura` — found, not found
    - `TestEliminarFactura` — success, no-op if not found, raises ValueError when documents attached
    - `TestObtenerTotalFacturacion` — returns sum, returns 0.0 when none
  - **Files:** `tests/test_billing.py`
  - **Dependencies:** 3.2, 4.2, 5.1–5.5 (in-memory repo + use cases)
