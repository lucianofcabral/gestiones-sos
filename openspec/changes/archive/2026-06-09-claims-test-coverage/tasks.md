# Tasks: Claims Test Coverage

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | 120-180 |
| 400-line budget risk | Low |
| Chained PRs recommended | No |
| Suggested split | Single PR |
| Delivery strategy | single-pr-default |

Decision needed before apply: No
Chained PRs recommended: No
Chain strategy: size-exception
400-line budget risk: Low

### Suggested Work Units

| Unit | Goal | Likely PR | Notes |
|------|------|-----------|-------|
| 1 | InMemorySosClaimRepository + FakeUnitOfWork + 3 tests | PR 1 | Single PR — all additive, no production code changes |

## Phase 1: Infrastructure — InMemorySosClaimRepository

- [x] 1.1 Create `src/adapters/persistence/inmemory_sos_claim_repository.py` implementing `BaseRepo[SosClaim] + _Activatable[SosClaim] + get_by_number() + get_claims_by_claim_id() + get_by_status() + get_by_text_like()`, mirroring `InMemoryClaimRepository` pattern

## Phase 2: Tests — RegistrarGestionSOS Scenarios

- [x] 2.1 Add `FakeUnitOfWork` inline class in `tests/test_claims.py` wrapping `InMemoryClaimRepository` + `InMemorySosClaimRepository` with no-op commit/rollback, subclassing `UnitOfWork` ABC
- [x] 2.2 Add fixtures (`inmemory_sos_claim_repo`, `fake_uow`) and seed helper (`_make_registrar_input`) in `tests/test_claims.py`
- [x] 2.3 Add `test_registrar_gestion_sos_happy` — valid input creates Claim + SosClaim, output has IDs, read-back verifies both in repos
- [x] 2.4 Add `test_registrar_duplicate_gestion_raises` — seed SosClaim with gestion=N, call execute with same N, assert `ValueError("Ya existe una gestión...")`
- [x] 2.5 Add `test_registrar_field_roundtrip` — populate all input fields, assert output DTO fields match (gestion, claimer_name, policy_number, plate)

## Phase 3: Verify

- [x] 3.1 Run `pytest tests/test_claims.py -v` — all 5 existing + 3 new tests pass
- [x] 3.2 Run `pytest tests/ -v` — no regressions in auth, payments, periods
