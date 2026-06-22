# Design: Payments CRUD — UI Layer

## Technical Approach

A dedicated `/pagos` single-page UI built with NiceGUI `ui.refreshable` (table) and `ui.dialog` + `ui.card` (modals), following the exact patterns from `facturacion.py` and `catalogos.py`. All domain dependencies are already wired in the container — zero backend changes. Agent UUIDs are resolved to names at render time via `agent_repo.get_by_ids()`. Filter state is held in local reactive variables within the page function.

## Architecture Decisions

| Decision | Choice | Alternatives | Rationale |
|----------|--------|-------------|-----------|
| Page pattern | Single file (`pagos.py`) with nested dialogs | Separate components file | Matches all existing pages; no routing complexity |
| Agent name resolution | Batch `get_by_ids()` at render time | Lazy per-row fetch | Existing `AgentRepoPort` supports batch; avoids N+1 |
| Filters | Client-side filter on `get_all()` result | Server-side SQL filtering | Payments are not paginated yet; `get_all()` returns manageable dataset |
| NC sub-section | Secondary dialog per payment row | Expandable inline row | Avoids layout complexity; dialog matches CRUD modal pattern |
| Update rules enforcement | Call `actualizar_pago.execute()` and catch exceptions | Pre-check in UI | Domain service already returns clear errors; UI shows them via `ui.notify` |
| Inactivate/Activate | Single button per row switching icon | Separate buttons | Follows `catalogos.py` switch pattern but uses button for explicit action with reason display |
| Create form NC section | Conditional `ui.select` for period that appears when payment_via=NC | Always-visible field | Reduces cognitive load; only relevant for NC payments |

## Data Flow

```
User action → UI handler → container.{use_case}.execute(input) → domain service validation → repo → response → notify() + refresh()

[Load page]
  ObtenerPagos.get_all() → list[Payment]
  AgentRepoPort.get_by_ids([all payer_ids + payee_ids]) → dict[UUID, name]
  PaymentViaRepoPort.get_all() → list[PaymentVia]
  → render table with resolved agent names

[Create]
  Form submit → RegistrarPago.execute(input) → RegistrarPagoOutput
  → on success: notify() + _table.refresh()
  → on error: notify(exception, type="negative")

[Edit]
  Open dialog with pre-filled values
  → ActualizarPago.execute(input) → ActualizarPagoOutput
  → on success: dialog.close() + notify() + _table.refresh()

[Inactivate]
  button → InactivarPago.execute(InactivarPagoInput) → InactivarPagoOutput
  → if !success: notify(reason, type="warning")
  → if success: notify(reason) + _table.refresh()

[Activate]
  button → ActivarPago.execute(ActivarPagoInput) → ActivarPagoOutput
  → same flow as inactivate
```

## File Changes

| File | Action | Description |
|------|--------|-------------|
| `src/ui/pages/pagos.py` | Modify | Replace placeholder with full CRUD page (~350 lines) |
| `main.py` | None | Already imports `register_pagos_page()` and calls it |

No other files change. Container already wires all dependencies.

## Interfaces / Contracts

No new interfaces. The page consumes existing use case contracts:

- **List**: `container.obtener_pagos.get_all() → list[Payment]`, `container.agent_repo.get_by_ids(ids) → list[Agent]`
- **Create**: `container.registrar_pago.execute(RegistrarPagoInput)` with fields: `claim_id`, `payer_id`, `payee_id`, `payment_via_id`, `amount`, `period_id?`
- **Edit**: `container.actualizar_pago.execute(ActualizarPagoInput)` with fields: `payment_id`, `payer_id?`, `payee_id?`, `payment_via_id?`, `amount?`
- **Inactivate**: `container.inactivar_pago.execute(InactivarPagoInput)` → `InactivarPagoOutput(success, reason)`
- **Activate**: `container.activar_pago.execute(ActivarPagoInput)` → `ActivarPagoOutput(success, reason)`
- **NC read**: `container.obtener_ncs.get_by_payment_id(payment_id) → CreditNote | None`
- **NC create**: `container.registrar_nc.execute(RegistrarNotaCreditoInput)`
- **NC inactivate**: `container.inactivar_nc.execute(InactivarNotaCreditoInput)`
- **NC mark delivered**: `container.marcar_nc_entregada.execute(MarcarNotaCreditoEntregadaInput)`

## Testing Strategy

| Layer | What to Test | Approach |
|-------|-------------|----------|
| Unit | Page function structure (N/A for NiceGUI) | Not applicable — NiceGUI pages are integration-only |
| Integration | All CRUD flows via simulated button clicks | Use `nicegui.testing` or manual `ui.run` tests; covered by acceptance criteria |
| E2E | Full create→edit→inactivate→activate cycle | Manual verification against acceptance criteria in proposal |
| Snapshot | Table rendering with mock data | Use `ui.page` + `Client` test helper if available |

## Migration / Rollout

No migration required. The placeholder is replaced atomically. Existing `/pagos` route continues to work — content changes only.

## Open Questions

None.
