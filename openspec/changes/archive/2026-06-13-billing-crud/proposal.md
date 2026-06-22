# Proposal: Billing CRUD — Invoices

## Intent

Invoice entity and `BillingRepoPort` exist but no persistence layer (stub always returns empty lists). This delivers the full stack — DB table, repos, use cases, and UI — so users can register and view invoices per period. Unblocks `PeriodRepoPort.get_total_billing_by_year_month()` and replaces the stub that `CanInactivatePaymentService` relies on.

## Scope

### In Scope
1. `invoices` table in `tables.py` + Alembic migration
2. `SqlAlchemyBillingRepository` implementing `BillingRepoPort` (+ `BaseRepo[Invoice]` + `_DocReachable[Invoice]`)
3. `InMemoryBillingRepository` for unit testing
4. Use cases: `RegistrarFactura`, `ObtenerFacturas`, `ObtenerFactura`, `EliminarFactura`, `ObtenerFacturasPorPeriodo`
5. Container wiring: replace `_StubBillingRepository` with real impl, wire use cases
6. `PeriodRepoPort.get_total_billing_by_year_month()` — implement in both SQLAlchemy and InMemory repos
7. UI page at `/facturas` (list per period + create form)
8. Sidebar nav: add "Facturas" link
9. Unit tests (`tests/test_billing.py` — in-memory pattern)

### Out of Scope
- Invoice editing (delete + re-create instead)
- Document attachment per invoice (exists separately via `DocumentTypeEnum.INVOICE`)
- Automatic invoice generation from NC aggregation
- PDF generation or emission
- `_Activatable` (Invoice has no active/inactive — once emitted it's permanent)

## Capabilities

### New
- `billing-crud`: Full CRUD for Invoice entities, listable by period, with `get_total_billing_by_year_month`.

### Modified
- `payment-inactivation-rule`: Replaces stub repo, but spec-level behavior unchanged (already depends on `get_by_period_id`).

## Approach

Mirror `Payment` repo pattern. `invoices` table: `invoice_id UUID PK`, `invoice_number INT NOT NULL`, `period_id UUID FK→periods`, `emited_date TIMESTAMP`, `amount NUMERIC(12,2)`, `created_at TIMESTAMP`. SQLAlchemy repo with `_get_conn` + `_row_to_model`. In-memory repo with `list[Invoice]`. Use cases as thin wrappers over repo calls. UI: NiceGUI `ui.table` filtered by period + inline create form. `get_total_billing_by_year_month` sums `amount` filtered by period. `invoice_number` approach depends on the business decision below.

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `src/infrastructure/database/tables.py` | Modified | +`invoices` table def |
| `alembic/versions/` | New | Migration: create `invoices` |
| `src/adapters/persistence/sqlalchemy_billing_repository.py` | New | SQLAlchemy `BillingRepoPort` impl |
| `src/adapters/persistence/inmemory_billing_repository.py` | New | In-memory `BillingRepoPort` impl |
| `src/application/use_cases/billing/` | New | CRUD use cases |
| `src/infrastructure/container.py` | Modified | Replace stub, wire repos + use cases |
| `src/adapters/persistence/sqlalchemy_period_repository.py` | Modified | Implement `get_total_billing_by_year_month` |
| `src/adapters/persistence/inmemory_period_repository.py` | Modified | Implement `get_total_billing_by_year_month` |
| `src/ui/pages/facturas.py` | New | List + create page |
| `src/ui/components/shell.py` | Modified | Add "Facturas" sidebar link |
| `main.py` | Modified | Register facturas page |
| `tests/test_billing.py` | New | In-memory tests |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Migration conflicts | Low | Target current head `c90154480bf3` |
| Numbering collision if per-period sequential | Low | `(period_id, invoice_number)` unique constraint |
| Amount precision (float vs Numeric) | Low | Use `Numeric(12,2)` in DB, `float` in domain (matches all existing entities) |

## Rollback Plan

`alembic downgrade -1` drops table. Revert changed files in reverse order. Replace real billing repo with `_StubBillingRepository` in container. No data loss risk — no production invoices exist.

## Dependencies

Current migration head `c90154480bf3`. Domain entity `Invoice` and `BillingRepoPort` exist. `PeriodRepoPort` exists but `get_total_billing_by_year_month` needs implementing.

## Success Criteria

- [ ] `alembic upgrade head` creates `invoices` table
- [ ] SQLAlchemy repo: `add`, `get_by_id`, `get_by_period_id`, `get_all`, `delete` all work
- [ ] In-memory repo: same methods + `_DocReachable` stubs
- [ ] 5 use cases execute correctly against in-memory repos
- [ ] `PeriodRepoPort.get_total_billing_by_year_month` returns correct sum
- [ ] Container replaces stub with `SqlAlchemyBillingRepository`
- [ ] `/facturas` renders list per period with create form; sidebar links to it
- [ ] `tests/test_billing.py` passes

## Open Questions

### 1. Invoice numbering: how should `invoice_number` be generated?

The domain has `invoice_number: int` with `ge=0`. Two options:

**A) Sequential per period** — reset to 1 each period, auto-assigned on creation. Requires `(period_id, invoice_number)` unique constraint. Mirrors real-world paper invoices where each period has its own series.

**B) Global auto-increment** — monotonically increasing across all periods. Simpler to implement (just `SELECT COALESCE(MAX(invoice_number), 0) + 1` or DB sequence), but doesn't match typical paper invoice series where periods have independent numbering.

### 2. Invoice ↔ CreditNote relationship

The domain model shows:
- `CreditNote` has a `period_id` (but no `invoice_id`)
- `CanInactivatePaymentService` checks "does period have invoices?" as a proxy for "is period closed?"

This suggests an Invoice represents a **period-level billing document** that "closes" a period by aggregating its NCs. But there are several possible interpretations:

**A) Period-closure invoice** — One Invoice per period = the total billing document that closes the period. All NC amounts in that period aggregate into this single invoice. Once emitted, the period is "closed" and NCs can't be inactivated.

**B) Individual billing events** — Multiple Invoices per period, each representing a separate billing event. An Invoice could be linked to a specific NC (but the entity has no `nc_payment_id` field — you'd add it or use the `DocumentEntity` cross-reference).

**C) Independent billing records** — Invoices are standalone records unrelated to NCs. The period link is just for organizational grouping. The `get_total_billing_by_year_month` is simply informational.

**D) One per NC cycle** — Each Invoice is created when a set of NCs for a period is ready to bill. There could be multiple invoices per period, one per "billing batch" of NCs.

Which model fits your business process?
