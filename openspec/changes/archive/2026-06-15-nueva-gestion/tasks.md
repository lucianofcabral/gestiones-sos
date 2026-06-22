# Tasks: nueva-gestion — New Claim Form

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | ~220 |
| 400-line budget risk | Low |
| Chained PRs recommended | No |
| Suggested split | Single PR |
| Delivery strategy | auto-forecast |

Decision needed before apply: No
Chained PRs recommended: No
Chain strategy: size-exception
400-line budget risk: Low

## Phase 1: Foundation — ObtenerClaimKinds Use Case

- [x] 1.1 Create `src/application/use_cases/claims/obtener_claim_kinds.py` — `ObtenerClaimKinds(repo: ClaimKindRepoPort)`, `execute() -> list[ClaimKind]`, mirrors `ObtenerGrupos`
- [x] 1.2 Create `tests/test_claim_kinds.py` — `TestObtenerClaimKinds` class with `test_get_all_returns_all` (seeded repo → len==N) and `test_get_all_returns_empty` (empty repo → []), using `InMemoryClaimKindRepository`

## Phase 2: Integration — Container Wiring

- [x] 2.1 Add imports in `container.py`: `ObtenerClaimKinds`, `RegistrarGestionSOS`, `SqlAlchemyUnitOfWork`
- [x] 2.2 In `Container.__init__`: init `_obtener_claim_kinds = ObtenerClaimKinds(_claim_kind_repo)` and `_registrar_gestion_sos = RegistrarGestionSOS(SqlAlchemyUnitOfWork())`
- [x] 2.3 Add `@property obtener_claim_kinds` and `@property registrar_gestion_sos` accessors to `Container`

## Phase 3: UI — Form Page

- [x] 3.1 Replace `gestiones_nueva.py` placeholder: import container, use cases, exceptions; on page init load `obtener_grupos.execute()` and `obtener_claim_kinds.execute()` into local state for dropdown options
- [x] 3.2 Render two `ui.card` sections inside `AppShell`: Claim Data (selects for claim_kind + group, inputs for claimer_name/policy_number/plate/claimed_amount/comment) and SOS Data (input for gestion, inputs for category/reason/load_user/response_user, status select with ABIERTO/CERRADO/RECHAZADO, input for itr)
- [x] 3.3 Add client-side validation on submit: check 7 required fields (claim_kind, group, claimer_name, policy_number, plate, gestion, status) — `ui.notify("Campo requerido...", type="warning")` and abort if missing
- [x] 3.4 Add submit handler: build `RegistrarGestionSOSInput` from form values, call `container.registrar_gestion_sos.execute(input)`, catch `GestionAlreadyExistsError` → notify negative, catch generic `Exception` → notify "Error al registrar gestión", on success → notify positive + `ui.navigate.to("/gestiones")`

## Verification

- [x] Run `pytest tests/test_claim_kinds.py` — 2 tests pass
- [x] Run `pytest tests/test_claims.py` — all 4 existing tests still pass (RegistrarGestionSOS unchanged)
- [x] Run full test suite to confirm no regressions from container changes
