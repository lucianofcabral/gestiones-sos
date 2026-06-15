# Tasks: Gestiones Listado

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | ~295 |
| 400-line budget risk | Low |
| Chained PRs recommended | No |
| Suggested split | Single PR |
| Delivery strategy | auto |

Decision needed before apply: No
Chained PRs recommended: No
Chain strategy: size-exception
400-line budget risk: Low

## Phase 1: Foundation — Use Case

- [x] 1.1 Create `src/application/use_cases/claims/obtener_gestiones.py` with `GestionDTO` (15 fields), `ObtenerGestionesOutput`, and `ObtenerGestiones` class
- [x] 1.2 Implement `ObtenerGestiones.execute(include_inactive=False)`: fetch all claims + sos_claims, join by `claim_id`, filter by active, map to DTOs

## Phase 2: Wiring — Container

- [x] 2.1 Import `SosClaimRepoPort` and `SqlAlchemySosClaimRepository` in `src/infrastructure/container.py`
- [x] 2.2 Add `_build_sos_claim_repo()` factory and `self._sos_claim_repo` in `Container.__init__`
- [x] 2.3 Add `sos_claim_repo` property exposing `SosClaimRepoPort`
- [x] 2.4 Import `ObtenerGestiones` and wire `self._obtener_gestiones = ObtenerGestiones(self._claim_repo, self._sos_claim_repo)` with property getter

## Phase 3: UI — Gestiones Page

- [x] 3.1 Rewrite `src/ui/pages/gestiones.py`: `@ui.refreshable` table with all 15 GestionDTO columns following `facturacion.py` pattern
- [x] 3.2 Add active/inactive toggle (default: active only) wired to `container.obtener_gestiones.execute(include_inactive=...)`
- [x] 3.3 Add delete button per row → confirmation `ui.dialog` → `container.eliminar_gestion_sos.execute()` → refresh table on success

## Phase 4: Testing

- [x] 4.1 Create `tests/test_claims_list.py` with `InMemoryClaimRepository` + `InMemorySosClaimRepository` fixtures
- [x] 4.2 Test: default `execute()` returns only active claims; `include_inactive=True` includes inactive ones
- [x] 4.3 Test: empty repos return `[]`; verify all `GestionDTO` fields map correctly from source entities
