# Proposal: Payments CRUD — UI Layer

## Intent

The domain layer for Payment CRUD (create, read, update, inactivate/activate) plus NC payment management is fully implemented and tested. The `/pagos` page is still a placeholder ("Próximamente — control de pagos"). This change delivers a dedicated, dialog-based CRUD UI so operators can manage payments without relying on the claim detail read-only table.

## Scope

### In Scope
- List view: `/pagos` page with payments table (payer, payee, amount, date, active status)
- Create dialog: form for new payment with Agent reference picker (payer/payee) and PaymentVia dropdown
- Edit dialog: update amount and optionally payer/payee/payment_via (respecting NC editability rules)
- Inactivate/Activate: inline toggle or dialog with reason display from domain service
- Agent name resolution: display payer/payee names (not UUIDs) in table and forms
- NC Payment management: sub-table or expandable section per payment row for linked credit notes
- Filter bar: by claim ID (exact match), date range, active/inactive status

### Out of Scope
- Bulk operations (multi-select, bulk inactivate)
- Export (CSV/PDF)
- Advanced search (fuzzy, full-text)
- Payment deletion (only soft-delete via inactivate)
- Batch NC creation
- Claim detail page payments section upgrade (read-only stays as-is)

## Capabilities

### New Capabilities
- `payment-ui`: Dedicated payments page with table, modals, filters, agent-name resolution, and NC management sub-section

### Modified Capabilities
- `payment-crud`: No spec-level change — domain layer already done. UI adds screens but no new business rules.
- `nc-payment-crud`: Same — domain layer complete. UI surfaces CRUD operations for NC linked to a payment.
- `payment-inactivation-rule`: No change — domain service already handles the rule.

## Approach

Dedicated `/pagos` page à la `facturacion.py`: a single-page catalog-style view with a reactive refreshable table and modal dialogs for create/edit. Agent names resolved from `AgentRepoPort` at render time using existing container wiring. NC management surfaces as an expandable sub-table or secondary dialog per payment row.

Pattern: `ui.refreshable` for the table (same as `catalogos.py`), `ui.dialog` with `ui.card` for modals (same pattern).

Order of delivery:
1. List view with agent name resolution
2. Create dialog
3. Edit dialog
4. Inactivate/Activate toggle
5. Filters
6. NC management sub-section

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `src/ui/pages/pagos.py` | Modified | Replace placeholder with full CRUD page |
| `src/ui/pages/gestiones_detalle.py` | None | Read-only payments table stays unchanged |
| Container wiring | None | All use cases and repos already wired |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Agent reference picker: no reusable component exists | Med | Build inline `ui.select` with async name resolution; extract later if reused |
| NC editability rules complex to surface in UI | Low | Domain service already returns clear error messages; show them in `ui.notify` |
| Filters add UI state management complexity | Low | Use local reactive variables within the refreshable function; pattern already in `facturacion.py` |

## Rollback Plan

Revert changes to `src/ui/pages/pagos.py` only. No migration, no DB changes, no container changes. The placeholder page is restored.

## Dependencies

- None. All domain services, use cases, and repositories are already wired in the container.

## Success Criteria

- [ ] `/pagos` renders a table of all payments with payer/payee names, not UUIDs
- [ ] Create payment dialog opens, submits, and new row appears without page reload
- [ ] Edit dialog respects NC editability rules (amount-only when NC exists; shows error otherwise)
- [ ] Inactivate/Activate toggles update the active status and refresh the table
- [ ] NC payments can be viewed and managed per payment
- [ ] Filters narrow results correctly
