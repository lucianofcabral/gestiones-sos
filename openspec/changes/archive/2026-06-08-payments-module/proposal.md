# Proposal: payments-module

## Intent

Deliver the payments domain module — entities, ports, domain service, use cases, repos, tables, and migration — so the system can register, query, and soft-delete payments with credit-note lifecycle rules. This also protects claim deletion from orphaned active payments.

## Scope

### In Scope
- `active` field on `Payment` entity (soft-delete, matching all other entities)
- `Payment` CRUD use cases: create, list, get-by-id, update, inactivate (same pattern as `EliminarGestionSOS`)
- `CanInactivatePaymentService` — domain service coordinating `NcPaymentRepoPort` + `BillingRepoPort` for the closed-period check
- Update `PaymentRepoPort` with `_Activatable` mixin + implement in both SQLAlchemy and in-memory repos
- Add `get_by_period_id` to `BillingRepoPort` (needed by the domain service) + implement in both repos
- `NcPayment` CRUD use cases (same pattern)
- Payment guard on `EliminarGestionSOS`: inject `PaymentRepoPort`, check `get_by_claim_id` before `inactivate()`, raise `ValueError` if active payments exist
- SQLAlchemy Core tables: `payments`, `nc_payments` in `tables.py`
- Alembic migration for both tables
- Unit tests for all use cases using in-memory repos
- Wire all new dependencies in `Container`

### Out of Scope
- UI pages for payment management (home link to `/pagos` exists but no pages requested)
- NiceGUI components or API routes
- Physical DELETE (soft-delete only)
- Domain-specific exception types (keep `ValueError`)
- Payment `update` via the domain service (update is a simple field change — no lifecycle rule needed)
- Integration/DB tests (unit tests with in-memory repos only)

## Capabilities

### New Capabilities
- `payment-crud`: Full CRUD + soft-delete for Payment entities — create, list, get-by-id, update, inactivate
- `payment-inactivation-rule`: Business rule — a Payment can be inactivated only if it has no NcPayment, or the NcPayment's period has no Invoice (period not closed)
- `nс-payment-crud`: CRUD for CreditNote entities linked to Payments and Periods — create, list, get-by-id, update, inactivate (soft-delete)

### Modified Capabilities
- `claim-deletion`: Adds payment guard — `EliminarGestionSOS` now raises `ValueError` if the claim has active payments

## Approach

1. **Entities** — Add `active: bool = True` to `Payment`. `CreditNote` already has no `active` field — add it for soft-delete consistency.
2. **Ports** — Add `_Activatable` to `PaymentRepoPort` and `NcPaymentRepoPort`. Add `get_by_period_id` to `BillingRepoPort`.
3. **Domain service** — `CanInactivatePaymentService` receives an `NcPaymentRepoPort` and `BillingRepoPort`. Returns `(can_inactivate: bool, reason: str)`. Logic: if no NcPayment for the Payment → can inactivate. If NcPayment exists and its period has NO Invoice → can inactivate. If period HAS Invoice → CANNOT inactivate (period is closed).
4. **Use cases** — Four use cases per entity (add, get, update, inactivate) + list (get_all). Each follows the existing pattern: explicit Input/Output DTOs, single `execute()` method, `ValueError` on not-found.
5. **Payment guard** — `EliminarGestionSOS` gains `payment_repo: PaymentRepoPort` parameter. Before `inactivate()`, calls `payment_repo.get_by_claim_id()` and checks all returned payments have `active=False`. Raises `ValueError` if any are active.
6. **Tables** — `payments` (FK→claims), `nc_payments` (FK→payments, FK→periods) with `active` columns.
7. **Repos** — SQLAlchemy + in-memory implementations per existing pattern. `Container` wires them.
8. **Tests** — Per use case, following `test_claims.py` pattern.

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `src/domain/models/entities.py` | Modified | Add `active` to Payment and CreditNote |
| `src/domain/ports/repositories.py` | Modified | Add `_Activatable` to Payment+NcPayment ports, `get_by_period_id` to Billing |
| `src/domain/services/can_inactivate_payment.py` | New | Domain service for the closed-period check |
| `src/application/use_cases/payments/` | New | CRUD use cases for Payment and NcPayment |
| `src/application/use_cases/claims/eliminar_gestion_sos.py` | Modified | Add payment guard |
| `src/adapters/persistence/sqlalchemy_payment_repository.py` | New | SQLAlchemy Core repo for Payment |
| `src/adapters/persistence/inmemory_payment_repository.py` | New | In-memory repo for Payment |
| `src/adapters/persistence/sqlalchemy_ncpayment_repository.py` | New | SQLAlchemy Core repo for NcPayment |
| `src/adapters/persistence/inmemory_ncpayment_repository.py` | New | In-memory repo for NcPayment |
| `src/adapters/persistence/sqlalchemy_billing_repository.py` | Modified | Add `get_by_period_id` |
| `src/adapters/persistence/inmemory_billing_repository.py` | Modified | Add `get_by_period_id` |
| `src/infrastructure/database/tables.py` | Modified | Add `payments` and `nc_payments` tables |
| `src/infrastructure/container.py` | Modified | Wire new repos and use cases |
| `alembic/versions/` | New | Migration for both tables |
| `tests/test_payments.py` | New | Unit tests for payment/NcPayment use cases |
| `tests/test_claims.py` | Modified | Update tests for payment guard |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| `BillingRepoPort.get_by_period_id` changes interface | Low | Follow same pattern as all other repos — pure additive |
| Payment guard changes EliminarGestionSOS contract | Low | Additive param with default — existing callers pass through |
| Domain service uses float for amount comparison | Low | Invoice.amount already has `gt=0` — period with any Invoice is "closed" |

## Rollback Plan

Revert migration, drop `payments` and `nc_payments` tables, revert all new files and modifications to existing files. Tests will fail after revert, confirming the rollback.

## Dependencies

- `EliminarGestionSOS` already wired in Container ✓
- `ClaimRepoPort`, `PaymentRepoPort`, `NcPaymentRepoPort`, `BillingRepoPort` exist ✓
- Alembic configured with `metadata` from `tables.py` ✓

## Success Criteria

- [ ] All 11 existing tests + new tests pass
- [ ] Payment CRUD works via in-memory repo tests (create, list, get-by-id, update, inactivate)
- [ ] NcPayment CRUD works via in-memory repo tests
- [ ] `CanInactivatePaymentService` returns correct verdict for all 3 scenarios (no NcPayment, NcPayment without Invoice, period closed)
- [ ] `EliminarGestionSOS` raises `ValueError` when claim has active payments
- [ ] Existing claim deletion (no payments) still succeeds
- [ ] Alembic migration generates both tables with FKs and defaults

## Proposal Question Round

A few items I want to validate before moving to specs:

1. **Payment `update` fields**: Should all Payment fields be updatable (payer, payee, amount, etc.) or only specific ones like `amount`? The `claim_id` and `payment_id` are identity fields — presumably read-only after creation.
2. **NcPayment `delivered` field**: Is `delivered` toggled via the update use case, or does it have its own dedicated operation (e.g., `mark_delivered`)?
3. **Home `/pagos` link**: It exists but has no page — should we leave it dead (no change), or wire a minimal placeholder page? The proposal currently says out of scope; confirm.
