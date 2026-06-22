# Proposal: Periods CRUD

## Intent

Period entity, table, repos, and container wiring exist but there's no unique constraint on `(year, month)` and no way to create, list, or delete periods through the UI. The placeholder page at `src/ui/pages/periodos.py` just shows "Próximamente". This delivers the full CRUD — DB constraint, use cases, and UI — so users can manage periods directly.

## Scope

### In Scope
1. Alembic migration: add `UniqueConstraint('year', 'month')` to `periods` table
2. Use case `CrearPeriodo` — create with duplicate guard (raise `ValueError` if `get_by_year_month` returns a match)
3. Use case `ListarPeriodos` — return all periods (wraps `get_all`)
4. Use case `EliminarPeriodo` — delete with referential integrity: check `billing_repo.get_by_period_id` and `nc_payment_repo.get_by_period_id`, raise `ValueError` with which entity blocks deletion
5. UI page at `/periodos` — year+month create form, period list (name, year, month), delete button with confirmation dialog
6. Container wiring — instantiate 3 use cases, expose as properties

### Out of Scope
- Edit (year/month identify the period — delete + re-create instead)
- Update use case (same reason)
- Changes to existing `Period` entity, repos, or ports

## Capabilities

### New
- `periods-crud`: Create, list, and delete Period entities with duplicate guard and referential integrity check against invoices and NCs.

### Modified
- None (pure add — existing specs unaffected)

## Approach

Mirror `Grupo` CRUD pattern. `CrearPeriodo` receives year+month, calls `period_repo.get_by_year_month` to guard duplicates, then `period_repo.add`. `EliminarPeriodo` receives period_id, checks `billing_repo.get_by_period_id` and `nc_payment_repo.get_by_period_id` for existing references, raises a descriptive `ValueError` if either returns data. UI replaces the placeholder with the same inline create + list + delete pattern used in `grupos.py`.

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `alembic/versions/` | New | Migration: `UniqueConstraint('year', 'month')` |
| `src/application/use_cases/periods/` | New | 3 use case files |
| `src/infrastructure/container.py` | Modified | Wire `CrearPeriodo`, `ListarPeriodos`, `EliminarPeriodo` |
| `src/ui/pages/periodos.py` | Modified | Replace placeholder with full UI |
| `src/infrastructure/database/tables.py` | Modified | Add `UniqueConstraint` to `periods` table |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Migration conflict during downgrade if unique constraint fails | Low | Target current head `27701ff330c2`; test downgrade |

## Rollback Plan

`alembic downgrade -1` drops the unique constraint. Revert changed files in reverse order. No data loss — the constraint only prevents duplicates, deletion removes no periods.

## Dependencies

Current migration head `27701ff330c2`. `PeriodRepoPort.get_by_year_month` already exists. `BillingRepoPort.get_by_period_id` and `NcPaymentRepoPort.get_by_period_id` already exist. `Period` entity has `year`, `month`, `period_name` properties.

## Success Criteria

- [ ] `alembic upgrade head` adds unique constraint; duplicate inserts fail at DB level
- [ ] `CrearPeriodo` creates a period and raises `ValueError` on duplicate (year, month)
- [ ] `ListarPeriodos` returns all periods
- [ ] `EliminarPeriodo` deletes a period with no references; raises `ValueError` with "facturas" or "notas de crédito" message if entities exist
- [ ] Container exposes all 3 use cases as properties
- [ ] `/periodos` renders create form + period list + delete buttons
