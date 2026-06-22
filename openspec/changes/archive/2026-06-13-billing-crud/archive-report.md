# Archive Report: Billing CRUD — Invoices

**Archived**: 2026-06-13
**Change**: billing-crud
**Verdict**: PASS WITH WARNINGS

## Change Summary

Full CRUD implementation for Invoice entities — create, list all/by period, view by ID, delete with referential integrity guard, and calculate period billing totals. Replaces the `_StubBillingRepository` that previously returned empty lists, unblocking `PeriodRepoPort.get_total_billing_by_year_month()` and the `CanInactivatePaymentService` inactivation rule. Invoice `invoice_number` changed from `int` to `str` (external code from SOS, not auto-generated). The full stack was delivered: DB table + Alembic migration, dual repos (SQLAlchemy + InMemory), 5 use cases, container wiring, UI page at `/facturas` with period selector + create form + total label, sidebar nav item, and 30 unit tests.

## Artifact Traceability

| Artifact | Filesystem | Engram ID |
|----------|------------|-----------|
| Proposal | `openspec/changes/archive/2026-06-13-billing-crud/proposal.md` | (to be saved) |
| Spec | `openspec/specs/billing-crud/spec.md` (kept as source of truth) | (to be saved) |
| Design | `openspec/changes/archive/2026-06-13-billing-crud/design.md` | (to be saved) |
| Tasks | `openspec/changes/archive/2026-06-13-billing-crud/tasks.md` | (to be saved) |
| Verify Report | `openspec/changes/archive/2026-06-13-billing-crud/verify-report.md` | (to be saved) |
| Archive Report | `openspec/changes/archive/2026-06-13-billing-crud/archive-report.md` | (this document) |

## Spec Sync Status

| Domain | Action | Details |
|--------|--------|---------|
| `billing-crud` | Confirmed (already in place) | `openspec/specs/billing-crud/spec.md` — 5 requirements, 12 scenarios. No delta spec existed in change folder (written directly to main specs). |

## Implementation Metrics

| Metric | Value |
|--------|-------|
| Tasks total | 17 |
| Tasks complete | 17 |
| Spec scenarios | 12 |
| Scenarios compliant | 11 / 12 (1 untested: FK violation — enforced at DB schema level) |
| Total tests | 313 passed (30 billing-specific) |
| New lint issues | 0 |
| Critical issues | 0 |
| Warnings | 1 (FK violation scenario untested — integration test not in current pattern) |
| Suggestions | 0 |

## Files Changed

| File | Action |
|------|--------|
| `alembic/versions/4b7e8d2f3c1a_create_invoices_table.py` | New |
| `main.py` | Modified |
| `openspec/changes/billing-crud/design.md` | New |
| `openspec/changes/billing-crud/proposal.md` | New |
| `openspec/changes/billing-crud/tasks.md` | New |
| `openspec/specs/billing-crud/spec.md` | New |
| `src/adapters/persistence/inmemory_billing_repository.py` | New |
| `src/adapters/persistence/inmemory_document_repository.py` | Modified |
| `src/adapters/persistence/inmemory_period_repository.py` | Modified |
| `src/adapters/persistence/sqlalchemy_billing_repository.py` | New |
| `src/adapters/persistence/sqlalchemy_claim_kind_repository.py` | Modified |
| `src/adapters/persistence/sqlalchemy_document_repository.py` | Modified |
| `src/adapters/persistence/sqlalchemy_group_claim_repository.py` | Modified |
| `src/adapters/persistence/sqlalchemy_payment_via_repository.py` | Modified |
| `src/adapters/persistence/sqlalchemy_period_repository.py` | Modified |
| `src/application/use_cases/billing/eliminar_factura.py` | New |
| `src/application/use_cases/billing/obtener_factura.py` | New |
| `src/application/use_cases/billing/obtener_facturas.py` | New |
| `src/application/use_cases/billing/obtener_total_facturacion.py` | New |
| `src/application/use_cases/billing/registrar_factura.py` | New |
| `src/domain/models/entities.py` | Modified |
| `src/domain/services/payment_update_rules.py` | Modified |
| `src/infrastructure/container.py` | Modified |
| `src/infrastructure/database/tables.py` | Modified |
| `src/infrastructure/storage/filesystem_storage.py` | Modified |
| `src/ui/components/shell.py` | Modified |
| `src/ui/pages/documentos.py` | Modified |
| `src/ui/pages/facturacion.py` | New |
| `src/ui/pages/grupos.py` | Modified |
| `tests/test_billing.py` | New |
| `tests/test_catalogos.py` | Modified |
| `tests/test_documents.py` | Modified |
| `tests/test_grupos.py` | Modified |
| `tests/test_payments.py` | Modified |
| `tests/test_periods.py` | Modified |
| `tests/test_ui_app_shell.py` | Modified |

## Key Decisions

1. **`invoice_number` as `str`** — Changed from `int` to `str` in the domain entity. External code from SOS is user-entered text, not an auto-generated integer sequence.
2. **Delete integrity via app-level check** — `EliminarFactura` checks `document_repo.get_by_billing_id()` before allowing deletion. Consistent with the GroupClaim pattern. No DB-level CASCADE.
3. **`get_total_billing` on PeriodRepo** — Implemented as a method on `PeriodRepoPort` (JPA queries invoices via JOIN or in-memory filtering), rather than a new port on BillingRepo. Follows the existing port definition.
4. **In-memory period repo receives invoice store** — `InMemoryPeriodRepository.__init__(invoice_store=...)` accepts a shared `list[Invoice]`. Follows the `InMemoryGroupClaimRepository(claim_store)` pattern.
5. **Table schema** — `invoices` table with `Numeric(12,2)` for amount, `String(50)` for invoice_number, FK to periods. No active/inactive flag (invoices are permanent once emitted).

## Dependencies

| Dependency | Type | Impact |
|------------|------|--------|
| `PeriodRepoPort.get_total_billing_by_year_month()` | Port method | Unblocked — was `NotImplementedError`, now fully implemented |
| `CanInactivatePaymentService` | Consumer | Now works with real repo data instead of empty stub lists |
| `DocumentRepoPort.get_by_billing_id()` | Referenced in delete guard | Must exist for `EliminarFactura` integrity check |
| Migration head `3a8f9c1e4b6d` | DB schema | Target head for the new migration |

## Open Items

1. **FK violation scenario untested**: The spec requires a scenario where `add` with a non-existent `period_id` raises an integrity error. The constraint exists in the schema (`sa.ForeignKey`), and SQLAlchemy raises at the DB level, but there is no covering unit test. Integration test not in the current pattern.

## SDD Cycle Complete

The change has been fully planned, implemented, verified, and archived. All artifacts are preserved in the archive for audit trail.
