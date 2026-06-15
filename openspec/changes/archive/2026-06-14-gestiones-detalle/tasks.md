# Tasks: Gestiones Detalle

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | ~390 |
| 400-line budget risk | Medium |
| Chained PRs recommended | No |
| Suggested split | Single PR |
| Delivery strategy | auto-forecast |
| Chain strategy | pending |

Decision needed before apply: No
Chained PRs recommended: No
Chain strategy: pending
400-line budget risk: Medium

### Suggested Work Units

| Unit | Goal | Likely PR | Notes |
|------|------|-----------|-------|
| 1 | Use case + DTOs + tests + container wiring | PR 1 | Backend-complete; testable via `pytest tests/test_claims_detail.py` |
| 2 | Detail page rewrite + row-click nav | PR 2 | Depends on PR 1 for the use case; pure UI work |

## Phase 1: Foundation — Use Case & DTOs

- [x] 1.1 Create `src/application/use_cases/claims/obtener_gestion_por_id.py` — DTOs (`ObtenerGestionPorIdInput`, `SosClaimDetailDTO`, `PaymentDTO`, `GestionDetalleDTO`) + `ObtenerGestionPorId` use case with 5 repo calls, `ClaimNotFoundError` raise, group/kind null→`""` fallback

## Phase 2: Wiring

- [x] 2.1 Wire `_obtener_gestion_por_id` in `src/infrastructure/container.py` — import, `__init__` instantiation, property accessor

## Phase 3: UI — Detail Page & Navigation

- [x] 3.1 Rewrite `src/ui/pages/gestiones_detalle.py` — 3-section layout (header card with claim info, SOS history table, payments table), back button to `/gestiones`, `ui.notify` error handling for `ClaimNotFoundError`
- [x] 3.2 Add `on_click` navigation to each row in `src/ui/pages/gestiones.py` — click row → `ui.navigate.to(f"/gestiones/{g.claim_id}")`

## Phase 4: Testing

- [x] 4.1 Create `tests/test_claims_detail.py` — 6 scenarios (happy path, claim not found, no SosClaims, no payments, missing group/kind, DTO type checks) with in-memory repo fixtures
