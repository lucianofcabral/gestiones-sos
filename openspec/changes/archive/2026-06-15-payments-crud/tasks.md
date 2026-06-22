# Tasks: Payments CRUD — UI Layer

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | 320–420 |
| 400-line budget risk | Low |
| Chained PRs recommended | No |
| Suggested split | Single PR |
| Delivery strategy | auto-forecast |

Decision needed before apply: No
Chained PRs recommended: No
Chain strategy: size-exception
400-line budget risk: Low

### Suggested Work Units

| Unit | Goal | Likely PR | Notes |
|------|------|-----------|-------|
| 1 | Full payments CRUD page in `pagos.py` | Single PR | Single file, autonomous, all-in-one |

## Phase 1: Page Foundation

- [x] 1.1 Add imports in `src/ui/pages/pagos.py` for container, entities (Payment, CreditNote, Agent, PaymentVia), use case Input/Output types, and domain services
- [x] 1.2 Replace placeholder body with `Container.get_instance()`, reactive filter state variables, and refreshable table scaffold

## Phase 2: Core CRUD Operations

- [x] 2.1 Implement refreshable payment list table — fetch all payments via `obtener_pagos.get_all()`, batch-resolve agent UUIDs via `agent_repo.get_by_ids()`, render columns: payer, payee, payment method, amount, date, active status
- [x] 2.2 Implement create payment dialog — form with claim_id, agent pickers for payer/payee, payment_via dropdown, amount, and conditional period_id field; call `registrar_pago.execute()` on submit; show validation errors via `ui.notify`
- [x] 2.3 Implement edit payment dialog — pre-fill fields from selected Payment; check `payment_update_rules` for NC-linked restrictions (disable payer/payee/via, show tooltip); call `actualizar_pago.execute()` on save
- [x] 2.4 Implement inactivate/activate per row — single button switching icon; call `can_inactivate_svc` / `can_activate_svc` first; show reason in confirmation or `ui.notify` if blocked

## Phase 3: Filters & NC Management

- [x] 3.1 Implement filter bar above table — claim_id (exact), date range (start/end), amount range (min/max), active/all toggle; client-side filter on `get_all()` results
- [x] 3.2 Implement NC sub-dialog per payment row — list linked CreditNotes; buttons for "Agregar NC" (period select + `registrar_nc.execute()`), mark delivered (`marcar_nc_entregada.execute()`), inactivate (`inactivar_nc.execute()`)

## Phase 4: Verification

- [x] 4.1 Manual smoke test — all 7 requirements against 16 spec scenarios: list view (empty + with data), create (transferencia + NC + validation), edit (without NC + with NC + non-existent), inactivate/activate (eligible + blocked + activate), agent resolution (found + missing), filters (claim, date, active), NC subsection (view, create, deliver, inactivate)
- [x] 4.2 Edge-case check — verify error notifications surface domain exception messages, verify conditional period field hides/shows correctly, verify graceful handling of missing agents ("—" display)
