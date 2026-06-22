# Archive Report: Periods CRUD

**Archived**: 2026-06-13
**Change**: periods-crud
**Verdict**: PASS

## Change Summary

Full CRUD (create-list-delete) for Period entities — duplicate guard on `(year, month)`, referential integrity checks against invoices and credit notes (NCs) before deletion, and a full UI replacing the "Próximamente" placeholder. Adds a `UniqueConstraint('year', 'month')` Alembic migration, three use cases (`CrearPeriodo`, `ListarPeriodos`, `EliminarPeriodo`), container wiring, and a `/periodos` page with create form + period list + delete buttons. 8 unit tests covering all spec scenarios — all pass.

## Artifact Traceability

| Artifact | Filesystem | Engram ID |
|----------|------------|-----------|
| Proposal | `openspec/changes/archive/2026-06-13-periods-crud/proposal.md` | (this archive) |
| Spec | `openspec/specs/periods-crud/spec.md` (kept as source of truth) | (this archive) |
| Design | `openspec/changes/archive/2026-06-13-periods-crud/design.md` | (this archive) |
| Tasks | `openspec/changes/archive/2026-06-13-periods-crud/tasks.md` | (this archive) |
| Verify Report | `openspec/changes/archive/2026-06-13-periods-crud/verify-report.md` | (this archive) |
| Archive Report | `openspec/changes/archive/2026-06-13-periods-crud/archive-report.md` | (this document) |

## Spec Sync Status

| Domain | Action | Details |
|--------|--------|---------|
| `periods-crud` | Confirmed (already in place) | `openspec/specs/periods-crud/spec.md` — 3 requirements, 8 scenarios. No delta spec existed in change folder (spec written directly to main specs). |

## Implementation Metrics

| Metric | Value |
|--------|-------|
| Tasks total | 11 |
| Tasks complete | 11 |
| Spec scenarios | 8 |
| Scenarios compliant | 8 / 8 |
| Total tests (periods-specific) | 8 passed |
| New lint issues | 0 |
| Critical issues | 0 |
| Warnings | 0 |
| Suggestions | 1 (design.md references outdated `down_revision` — see verify report) |

## Files Changed

| File | Action |
|------|--------|
| `alembic/versions/5c9d8e4f2b1a_add_unique_constraint_on_periods_year_month.py` | New |
| `src/application/use_cases/periods/__init__.py` | New |
| `src/application/use_cases/periods/crear_periodo.py` | New |
| `src/application/use_cases/periods/eliminar_periodo.py` | New |
| `src/application/use_cases/periods/listar_periodos.py` | New |
| `src/infrastructure/container.py` | Modified |
| `src/infrastructure/database/tables.py` | Modified |
| `src/ui/pages/periodos.py` | Modified (replaced placeholder) |
| `tests/test_periods_crud.py` | New |

## Key Decisions

1. **`UniqueConstraint` over app-level check** — Instead of guarding duplicates only in the use case, the constraint is also enforced at the DB schema level via Alembic migration. Prevents race-conditional duplicates and enforces consistency even if repos are used directly.
2. **App-level referential integrity for delete** — `EliminarPeriodo` checks `billing_repo.get_by_period_id()` and `nc_payment_repo.get_by_period_id()` before allowing deletion, raising descriptive Spanish errors. Same pattern as `EliminarGrupo` and `EliminarFactura`.
3. **Inner Pydantic Input/Output models** — Consistent with `RegistrarFactura` and `RegistrarPago` patterns. Input validated via `Field(ge=..., le=...)`.
4. **Hardcoded month names in UI** — `_MESES_ES` list defined in the page module rather than importing from domain (the domain's mapping is private).
5. **`down_revision` updated** — Design specified `27701ff330c2` but tasks and implementation correctly used `4b7e8d2f3c1a` (the billing migration head that was applied first).

## Dependencies

| Dependency | Type | Impact |
|------------|------|--------|
| `PeriodRepoPort.get_by_year_month()` | Port method | Used by `CrearPeriodo` for duplicate guard |
| `BillingRepoPort.get_by_period_id()` | Port method | Used by `EliminarPeriodo` for integrity check |
| `NcPaymentRepoPort.get_by_period_id()` | Port method | Used by `EliminarPeriodo` for integrity check |
| Migration head `4b7e8d2f3c1a` | DB schema | Target head for the new migration |
| `Period` entity | Domain model | Provides `year`, `month`, `period_name` properties |

## Open Items

None. All 8 spec scenarios are covered by passing tests, no warnings or critical issues.

## SDD Cycle Complete

The change has been fully planned, implemented, verified, and archived. All artifacts are preserved in the archive for audit trail.
