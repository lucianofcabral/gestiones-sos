# Proposal: Gestiones Detalle

## Intent

`/gestiones/{id}` is a placeholder. The list page shows only the "last" SosClaim per claim (dict overwrite) — agents cannot inspect all SosClaim records, payments, or group/kind names per claim. Blocks triage and payment reconciliation.

## Scope

### In Scope
- `ObtenerGestionPorId` use case: fetch Claim by ID + all SosClaims, payments, group name, claim kind name
- `ClaimDetalleDTO` with claim header, sos_records[], payments[], group_name, claim_kind_name
- `/gestiones/{id}` page: back nav, sectioned layout (claim info, SOS history table, payments table)
- Row-click nav from list to detail page
- Error state: `ui.notify` on ClaimNotFoundError

### Out of Scope
- Documents (v2), Agent/PaymentVia name resolution (raw IDs in v1), inline editing, payment CRUD from detail

## Capabilities

### New Capabilities
- `claim-detail`: Fetch full claim detail by ID — all SosClaims, payments, group/kind names

### Modified Capabilities
- `claim-listing`: Add row click → navigate to `/gestiones/{id}`

## Approach

1. **Use case** — `ObtenerGestionPorId(claim_repo, sos_claim_repo, group_claim_repo, claim_kind_repo, payment_repo)` — 5 repo calls, assemble DTO
2. **DTO** — `ClaimDetalleDTO` with nested `SosClaimDTO` + `PaymentDTO`
3. **UI** — Rewrite `gestiones_detalle.py` — extract `id`, call use case, render 3 sections (header card, SOS table, payments table) + back link
4. **Nav** — `on_click` on each row in `gestiones.py` → `ui.open(f"/gestiones/{claim_id}")`
5. **DI** — Wire `_obtener_gestion_por_id` in Container

## Affected Areas

| Area | Impact |
|------|--------|
| `src/application/use_cases/claims/obtener_gestion_por_id.py` | **New** |
| `src/ui/pages/gestiones_detalle.py` | **Modified** (full rewrite) |
| `src/ui/pages/gestiones.py` | **Modified** (add row click) |
| `src/infrastructure/container.py` | **Modified** (wire use case) |
| `src/application/use_cases/claims/__init__.py` | **Modified** (export) |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Payment agent/via resolution N+1 | Med | Defer to v2 |
| Long SOS list scroll | Low | Scrollable section |
| Stale nav → ClaimNotFoundError | Low | `ui.notify` + redirect |

## Rollback Plan

1. Remove `obtener_gestion_por_id.py`
2. Revert `gestiones_detalle.py` → placeholder
3. Revert row-click in `gestiones.py`
4. Remove container wiring
5. Verify placeholder restores

## Dependencies

- `GroupClaimRepoPort.get_by_claim_id()` ✅
- `ClaimKindRepoPort.get_by_id()` ✅
- `PaymentRepoPort.get_by_claim_id()` ✅
- `SosClaimRepoPort.get_claims_by_claim_id()` ✅

## Success Criteria

- [ ] `/gestiones/{id}` shows claim header, group/kind name, all SosClaim records
- [ ] Payments section shows payments (raw IDs)
- [ ] Row click navigates from list to detail
- [ ] Missing claim → error notification
- [ ] All existing tests pass
