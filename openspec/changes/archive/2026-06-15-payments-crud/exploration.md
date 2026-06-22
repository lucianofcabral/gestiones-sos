## Exploration: Payments CRUD

### Current State

#### Domain Model (`src/domain/models/entities.py`)
- **`Payment`** — fields: `payment_id` (UUID), `claim_id` (UUID, FK→claims), `payer_id` (UUID, ref→Agent), `payment_via_id` (UUID, ref→PaymentVia), `payee_id` (UUID, ref→Agent), `amount` (float, `gt=0`), `active` (bool, default True), `created_date` (datetime).
- **`CreditNote`** (aka NcPayment) — fields: `nc_payment_id`, `payment_id` (FK→payments), `period_id` (FK→periods), `delivered`, `active`, `created_date`.
- Relationship: **Claim 1→N Payments**. Payment.claim_id references Claim.claim_id.

#### Persistence
- **Table** (`src/infrastructure/database/tables.py`): `payments` table with matching columns, FK to `claims.claim_id`. `nc_payments` table with FK to `payments.payment_id` and `periods.period_id`.
- **Migration** (`alembic/versions/c90154480bf3`): creates both `payments` and `nc_payments` tables.
- **Repository protocol** (`src/domain/ports/repositories.py`): `PaymentRepoPort` extends `BaseRepo[Payment]` + `_Activatable[Payment]`, adding: `deleteable()`, `inactivatable()`, `get_by_claim_id()`, `get_by_date_range()`, `get_by_amount_range()`.
- **SQLAlchemy impl** (`SqlAlchemyPaymentRepository`): full CRUD using SQLAlchemy Core, supports external connection (UoW pattern via optional `conn` kwarg).
- **InMemory impl** (`InMemoryPaymentRepository`): for testing, same interface.
- **Same pattern for NcPayment**: `NcPaymentRepoPort`, `SqlAlchemyNcPaymentRepository`, `InMemoryNcPaymentRepository`.

#### Use Cases (`src/application/use_cases/payments/`)
All fully implemented and tested (protcol dependencies injected via constructor):

| Use Case | File | Operation |
|----------|------|-----------|
| `RegistrarPago` | `registrar_pago.py` | Create payment + optional NC creation |
| `ObtenerPagos` | `obtener_pagos.py` | Query: `get_by_id`, `get_all`, `get_by_claim_id` |
| `ActualizarPago` | `actualizar_pago.py` | Update with editability rule enforcement |
| `InactivarPago` | `inactivar_pago.py` | Soft-delete with inactivation eligibility check |
| `ActivarPago` | `activar_pago.py` | Reactivate with claim-active gate |
| `RegistrarNotaCredito` | `registrar_nc.py` | Create credit note |
| `ObtenerNotasCredito` | `obtener_ncs.py` | Query credit notes |
| `MarcarNotaCreditoEntregada` | `marcar_nc_entregada.py` | Mark NC as delivered |
| `InactivarNotaCredito` | `inactivar_nc.py` | Soft-delete NC |
| `ActivarNotaCredito` | `activar_nc.py` | Reactivate NC |

#### Domain Services
- **`CanInactivatePaymentService`** — checks if payment's NC-linked period has invoices (closed period blocks inactivation).
- **`CanActivatePaymentService`** — checks if the claim is active before reactivating.
- **`PaymentUpdateRules`** — validates update editability: no NC → all fields editable but can't switch to NC-via; NC exists → only amount editable.

#### UI — What Exists
- **Navigation**: Sidebar has "Pagos" item linking to `/pagos`.
- **Placeholder** (`src/ui/pages/pagos.py`): Shows only "Pagos — Próximamente, control de pagos."
- **Read-only display** (`src/ui/pages/gestiones_detalle.py`): Payments shown in claim detail as a read-only table (amount, date, active status).
- **Catalog CRUD pattern** (`src/ui/pages/catalogos.py`): Inline-editable table with name editing, active toggle, and delete confirmation — reference pattern for simple CRUD.

#### Container (`src/infrastructure/container.py`)
- All payment repos, domain services, and use cases are already wired as singleton properties on `Container` (manual DI, no framework).

#### Tests (`tests/test_payments.py`)
- 1225 lines covering entity validation, all 3 domain services, all 10 use cases, and claim-deletion guard.
- Uses `InMemoryPaymentRepository`, `InMemoryNcPaymentRepository`, `InMemoryClaimRepository` and minimal stubs.

#### Existing Specs on Filesystem
- `openspec/specs/payment-crud/spec.md` — requirements for Payment CRUD (create, query, update, activate/inactivate).
- `openspec/specs/nc-payment-crud/spec.md` — requirements for CreditNote CRUD.
- `openspec/specs/payment-inactivation-rule/spec.md` — domain service spec.
- Archived change `2026-06-10-payments-crud` — added `ActualizarPago`, `ActivarPago`, `PaymentUpdateRules`, `CanActivatePaymentService`.

### Affected Areas

- `src/ui/pages/pagos.py` — Replace placeholder with full payment list page (create, list, filter, edit, soft-delete).
- `src/ui/pages/gestiones_detalle.py` — May need to wire create/edit actions from claim detail context.
- `src/infrastructure/container.py` — Already wired; may need to expose additional use cases as properties if not already done.
- `main.py` — Already registers `register_pagos_page()`; no change needed.
- `tests/` — Add UI/integration tests if applicable.

### Approaches

1. **Catalog-style inline CRUD** — Replicate the pattern from `catalogos.py`: a single page with inline-editable rows, add form, delete confirmation, and active toggle.
   - Pros: Follows existing pattern, minimal new concepts, quick to implement.
   - Cons: Payments have more fields than catalogs (amount, payer, payee, payment_via, claim, date); inline editing for many columns gets cluttered; need to resolve reference fields (Agent, PaymentVia) into human-readable names; does not scale for filtering or bulk operations.
   - Effort: **Medium**

2. **Dedicated management page with dialog-based CRUD** — Full `/pagos` page with a table view, a "New Payment" button opening a form dialog, inline edit triggered by row click or edit button, and action buttons for activate/inactivate/delete.
   - Pros: Scales better for complex entities with multiple reference fields; proper UX for filtering/searching; clean separation between list and edit views.
   - Cons: More code than approach 1; dialog forms need field validation and reference pickers (Agent dropdown, PaymentVia dropdown, claim search).
   - Effort: **Medium-High**

3. **Embedded in claim detail only** — Add create/edit/delete actions directly in the payments section of `gestiones_detalle.py`, without a standalone `/pagos` page.
   - Pros: Context-relevant (payments always belong to a claim); simplest implementation; uses existing page structure.
   - Cons: No global payments view; can't see all payments across claims; sidebar "Pagos" link stays as placeholder or gets repurposed; limited filtering/search.
   - Effort: **Low-Medium**

### Recommendation

**Approach 2 (Dedicated page with dialog-based CRUD)** — The standalone `/pagos` page exists as a placeholder with a nav link already in the sidebar. Leaving it as "Próximamente" while users can only see payments inside claim detail is a poor UX. A dedicated page allows:
- Listing all payments with search/filter by claim, date range, amount range
- Creating payments outside claim detail context
- Managing NC delivery status
- Following the same dialog-over-table pattern already hinted by the project's UX (NiceGUI-based)

The pattern to follow is similar to `gestiones.py` (list view) + `gestiones_nueva.py` (create dialog), adapted for the simpler payment entity.

**Priority order for UI**: List view → Create dialog → Edit dialog (inline or modal) → Inactivate/Activate actions → Filter/search → NC management (mark delivered).

### Risks

- **Payer/payee resolution**: The model stores `payer_id` and `payee_id` as UUIDs (references to Agent). The UI needs to resolve these to display names. This requires additional lookups via `AgentRepoPort` or denormalization in the DTO.
- **Payment-via-dependent logic**: NC payments have extra constraints (SOS/SM agents, period requirement) that the creation form must surface conditionally.
- **No existing UI pattern for reference pickers**: The current codebase uses simple inputs/dropdowns but doesn't have a reusable "search for Agent" or "search for Claim" component. This may need to be built.
- **Filter complexity**: Date range, amount range, and claim filter add non-trivial UI state management.

### Ready for Proposal

**Yes** — The domain layer is fully implemented, tested, and wired. The gap is exclusively the UI layer. The exploration has identified three clear approaches, reference patterns, and the mapping to existing specs. The orchestrator should propose the UI implementation for the `/pagos` page.
