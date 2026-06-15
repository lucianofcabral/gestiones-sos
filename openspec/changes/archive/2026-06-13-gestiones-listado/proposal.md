# Proposal: Gestiones List Page

## Intent

Support agents need a centralized browsable list of all claims (gestiones) at `/gestiones`. Today there's only a placeholder and ad-hoc navigation — no single place to review, filter, or soft-delete claims. This impacts daily triage and cleanup workflows.

## Scope

### In Scope
- New `ObtenerGestiones` use case: fetches all Claims + SosClaims from both repos, joins in-memory on claim ID, returns `list[ClaimDetailDTO]`
- `/gestiones` page with `@ui.refreshable` table following `facturacion.py` pattern
- Default filter: active claims only, with toggle to include inactive
- Delete action via existing `EliminarGestionSOS`
- 13 columns: gestion#, claimer_name, policy_number, plate, claimed_amount, category, reason, status, load_user, created_at, solved, active

### Out of Scope
- "Nueva Gestión" page (separate change, needs UoW)
- Claim detail page / drill-down
- Server-side pagination
- Repository or port changes

## Capabilities

### New Capabilities
- `claim-listing`: List all claims with DTO joining, default active filter, and soft-delete action wired from the UI

### Modified Capabilities
- None — `claim-deletion` behavior is unchanged; the list page only calls the existing use case

## Approach

1. **Use case**: Create `src/application/use_cases/obtener_gestiones.py` — calls `claim_repo.get_all()` + `sos_claim_repo.get_all()`, joins by claim ID, maps to `ClaimDetailDTO`, applies active filter by default
2. **UI**: Rewrite `src/ui/pages/gestiones.py` — replace placeholder with `@ui.refreshable` table, active/inactive toggle, delete button wired to `container.eliminar_gestion_sos`, error display on payment-guard rejection
3. **Routing**: Verify `main.py` already registers the page (stated — verify during apply)

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `src/application/use_cases/` | **New** | `obtener_gestiones.py` — `ObtenerGestiones` use case |
| `src/ui/pages/gestiones.py` | **Modified** | Full rewrite of placeholder page |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| In-memory join performs poorly with many records | Low (current volume) | Monitor; pagination deferred to future change |
| Delete triggers error on claims with active payments | Low | `EliminarGestionSOS` already handles this; surface error as ui.notify |

## Rollback Plan

1. Remove `obtener_gestiones.py` from use cases folder
2. Revert `gestiones.py` to the old placeholder content
3. If `main.py` was touched, restore the original route registration
4. Verify `/gestiones` returns to placeholder state

## Dependencies

- None — `ClaimRepoPort`, `SosClaimRepoPort`, and `EliminarGestionSOS` are already wired in the container

## Success Criteria

- [ ] `/gestiones` loads and displays all active claims in a table with correct columns
- [ ] Toggle includes inactive claims and table updates
- [ ] Delete button calls `EliminarGestionSOS`, soft-deletes the claim, and table refreshes
- [ ] Errors (e.g., claim has active payments) shown as `ui.notify` notification
- [ ] All existing tests pass with no regressions
