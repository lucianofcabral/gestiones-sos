# Tasks: Periods CRUD

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | ~300–400 |
| 400-line budget risk | Low |
| Review budget (custom) | 800 lines |
| Chained PRs recommended | No |
| Suggested split | Single PR |
| Delivery strategy | single-pr |
| Chain strategy | size-exception |

Decision needed before apply: No
Chained PRs recommended: No
Chain strategy: size-exception
400-line budget risk: Low

### Suggested Work Units

| Unit | Goal | Likely PR | Notes |
|------|------|-----------|-------|
| 1 | Full Periods CRUD stack — migration → use cases → container → UI → tests | PR 1 | Single PR, same pattern as billing-crud (size-exception precedent) |

## Phase 1: Infrastructure / Database

- [x] 1.1 Add `sa.UniqueConstraint('year', 'month', name='uq_periods_year_month')` to `periods` table in `src/infrastructure/database/tables.py`
  - **Files:** `src/infrastructure/database/tables.py`
  - **Dependencies:** None

- [x] 1.2 Create Alembic migration: `alembic/versions/5c9d8e4f2b1a_add_unique_constraint_on_periods_year_month.py`
  - `down_revision = "4b7e8d2f3c1a"` (current head — billing migration)
  - `upgrade()`: `op.create_unique_constraint('uq_periods_year_month', 'periods', ['year', 'month'])`
  - `downgrade()`: `op.drop_constraint('uq_periods_year_month', 'periods')`
  - **Files:** `alembic/versions/xxxxxxxxxxxx_add_unique_constraint_periods.py`
  - **Dependencies:** 1.1 (table constraint def)

## Phase 2: Use Cases

- [x] 2.1 Create `src/application/use_cases/periods/crear_periodo.py`
  - `CrearPeriodo` — `Input(year, month)`, `Output(period)`
  - `execute`: calls `period_repo.get_by_year_month(year, month)` → raises `ValueError("Ya existe un período para ese año y mes")` if found
  - Creates `Period` entity with generated `period_name` (Spanish month + year), calls `period_repo.add()`
  - **Files:** `src/application/use_cases/periods/crear_periodo.py`
  - **Dependencies:** None (period repo port already exists)

- [x] 2.2 Create `src/application/use_cases/periods/listar_periodos.py`
  - `ListarPeriodos` — `Output(periods: list[Period])`
  - `execute`: calls `period_repo.get_n_last(None)` — returns all periods
  - **Files:** `src/application/use_cases/periods/listar_periodos.py`
  - **Dependencies:** None

- [x] 2.3 Create `src/application/use_cases/periods/eliminar_periodo.py`
  - `EliminarPeriodo` — `Input(period_id)`, `Output(deleted: bool)`
  - `execute`: get period by ID → return `Output(deleted=False)` if None
  - Check `billing_repo.get_by_period_id(period_id)` → raise `ValueError("No se puede eliminar: el período tiene facturas asociadas")` if invoices exist
  - Check `nc_payment_repo.get_by_period_id(period_id)` → raise `ValueError("No se puede eliminar: el período tiene notas de crédito asociadas")` if NCs exist
  - Delete via `period_repo.delete(period_id)`, return `Output(deleted=True)`
  - **Files:** `src/application/use_cases/periods/eliminar_periodo.py`
  - **Dependencies:** None (billing_repo, nc_payment_repo ports already exist)

## Phase 3: Container Wiring

- [x] 3.1 Add 3 use case properties to `src/infrastructure/container.py`
  - Import `CrearPeriodo`, `ListarPeriodos`, `EliminarPeriodo`
  - `self._crear_periodo = CrearPeriodo(self._period_repo)`
  - `self._listar_periodos = ListarPeriodos(self._period_repo)`
  - `self._eliminar_periodo = EliminarPeriodo(self._period_repo, self._billing_repo, self._nc_payment_repo)`
  - Add `@property` accessors for all 3
  - **Files:** `src/infrastructure/container.py`
  - **Dependencies:** 2.1, 2.2, 2.3 (all use cases created)

## Phase 4: UI Page

- [x] 4.1 Replace `src/ui/pages/periodos.py` placeholder with full CRUD page
  - `@ui.page("/periodos")` with `register_periodos_page()`
  - Uses `AppShell` for layout
  - Create form: year (`ui.number` or `ui.input`), month (`ui.select` 1-12), `ui.button("Crear")`
  - Period list (`ui.table`) — columns: name, year, month, actions
  - Delete buttons per row with confirmation dialog and error handling (`ui.notify` for integrity errors)
  - Refresh table on create / delete
  - **Files:** `src/ui/pages/periodos.py`
  - **Dependencies:** 3.1 (container wired)

## Phase 5: Tests

- [x] 5.1 Create `tests/test_periods_crud.py`
  - Use in-memory period/billing/nc-payment repos as injected deps
  - **CrearPeriodo tests:** success case (creates period), duplicate guard (raises ValueError)
  - **ListarPeriodos tests:** returns all periods, returns empty list when none
  - **EliminarPeriodo tests:** success (deletes period), not found (returns False), billing guard (ValueError with "facturas"), NC payment guard (ValueError with "notas de crédito")
  - **Files:** `tests/test_periods_crud.py`
  - **Dependencies:** 2.1, 2.2, 2.3 (use cases), in-memory repos (already exist)

## Phase 6: Lint + Verify

- [x] 6.1 Run `ruff check src/ tests/` — fix any issues
- [x] 6.2 Run `pytest tests/` — all tests pass
  - **Files:** None (verification step)
  - **Dependencies:** 1.1–5.1 (all prior tasks complete)
