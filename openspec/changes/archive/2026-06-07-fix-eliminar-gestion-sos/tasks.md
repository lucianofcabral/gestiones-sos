# Tasks: Fix EliminarGestionSOS — Replace copy-paste bug with proper soft-delete

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | ~100–120 |
| 400-line budget risk | Low |
| Chained PRs recommended | No |
| Suggested split | Single PR |
| Delivery strategy | ask-on-risk |
| Chain strategy | pending |

Decision needed before apply: No
Chained PRs recommended: No
Chain strategy: pending
400-line budget risk: Low

### Suggested Work Units

| Unit | Goal | Likely PR | Notes |
|------|------|-----------|-------|
| 1 | Rewrite use case, wire container, add tests | PR 1 | Single PR, ~100–120 lines total |

## Phase 1: Core Implementation

- [x] 1.1 Rewrite `src/application/use_cases/claims/eliminar_gestion_sos.py` — replace RegistrarGestionSOS copy-paste with `EliminarGestionSOSInput` (claim_id: UUID), `EliminarGestionSOSOutput` (claim_id, success), and `EliminarGestionSOS(claim_repo: ClaimRepoPort)` that calls `claim_repo.get_by_id()` → `claim_repo.inactivate()` → returns output. Raise `ValueError` if claim not found.

## Phase 2: Wiring

- [x] 2.1 Add `from src.adapters.persistence.postgresql_claim_repository import PostgreSQLClaimRepository` and `from src.application.use_cases.claims.eliminar_gestion_sos import EliminarGestionSOS` to `src/infrastructure/container.py`, then add `PostgreSQLClaimRepository` as a property and `EliminarGestionSOS` as a property wired with the claim repo.

## Phase 3: Testing

- [x] 3.1 Create `tests/test_claims.py` — add an `InMemoryClaimRepository` fixture, a helper to seed a claim, then test: create claim → delete → assert `claim.active is False` on read-back.
- [x] 3.2 Add test: call `EliminarGestionSOS.execute()` with a random UUID → assert `ValueError` with "not found".
- [x] 3.3 Add test: delete twice → both calls return `success=True` (idempotency).
