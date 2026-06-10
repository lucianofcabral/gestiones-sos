# Proposal: Claims Test Coverage

## Intent

Add pytest unit tests for the claims use cases (`RegistrarGestionSOS` and `EliminarGestionSOS`) using in-memory fakes. `EliminarGestionSOS` has 5 tests, `RegistrarGestionSOS` has **zero** — this gap blocks refactoring and creates risk.

## Scope

### In Scope
- `InMemorySosClaimRepository` — in-memory fake for `SosClaimRepoPort` (needed by both use cases)
- `FakeUnitOfWork` — lightweight in-memory UOW with `claims` + `sos_claims` attributes for `RegistrarGestionSOS`
- `RegistrarGestionSOS` tests: happy path (creates Claim + SosClaim atomically), duplicate gestion number rejection, field assertion for output DTO
- `EliminarGestionSOS` gap tests: verify existing `claim-deletion` spec scenarios that aren't yet covered (if any)
- Fix `ModuleNotFoundError: No module named 'src'` if PYTHONPATH is misconfigured

### Out of Scope
- Integration tests with SQLAlchemy / real DB
- UI/NiceGUI tests for claim screens
- Performance or load tests
- New specs or spec changes (pure test addition)

## Capabilities

### New Capabilities
None — this is a test-coverage-only change. No new business behavior is introduced.

### Modified Capabilities
None — existing specs (`claim-deletion`) are already correct. Tests will validate them.

## Approach

Follow the existing pattern from `test_auth.py` and `test_payments.py`:

1. **Fakes**: Add `InMemorySosClaimRepository` in `src/adapters/persistence/` (parallel to `InMemoryClaimRepository`). Add `FakeUnitOfWork` in tests or adapters.
2. **Fixtures**: Define `@pytest.fixture` per repo/UOW in `tests/test_claims.py`. Use `conftest.py` only if fixtures grow beyond one file.
3. **Helpers**: Factory functions (`_seed_claim`, `_make_input`) with sensible defaults, same pattern as `_payment()` in `test_payments.py`.
4. **Tests**: One function per scenario — happy path, edge case, error path. Verify output DTO fields and read-back state.
5. **PYTHONPATH**: Verify `pyproject.toml` has `pythonpath = ["."]` — if the module error persists after a clean install, fix it.

### Test scenarios for `RegistrarGestionSOS`
| Scenario | Expected |
|----------|----------|
| GIVEN valid input WHEN execute THEN claim + sos_claim are created, output has IDs | Success |
| GIVEN duplicate gestion number WHEN execute THEN ValueError | Error |
| GIVEN input with all fields WHEN execute THEN all output fields match | Field round-trip |

### Test scenarios for `EliminarGestionSOS` (gap coverage)
| Scenario | Expected |
|----------|----------|
| GIVEN no `payment_repo` WHEN execute THEN works (backward compat) | Success |
| GIVEN no Payments WHEN execute THEN claim inactivated (spec) | Success |

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `src/adapters/persistence/inmemory_sos_claim_repository.py` | New | In-memory SosClaimRepoPort fake |
| `tests/test_claims.py` | Modified | Add RegistrarGestionSOS tests + gap tests |
| `pyproject.toml` | Maybe fix | PYTHONPATH if ModuleNotFoundError persists |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| InMemorySosClaimRepository diverges from SQL impl | Low | Keep API exactly matching `SosClaimRepoPort` protocol |
| Existing tests break after changes | Low | Run full test suite before/after |

## Rollback Plan

Revert the single commit — `git revert HEAD`. All changes are additive, no schema or production code changes.

## Dependencies

- Python 3.13, pytest 9.0.3 (already in `uv.lock`)
- In-memory repos already exist for Claim, Payment, Period
- No external services needed

## Success Criteria

- [ ] `pytest tests/test_claims.py -v` passes (all 5 existing + new tests)
- [ ] `pytest tests/ -v` passes (no regressions in auth, payments, periods)
- [ ] `ModuleNotFoundError` for 'src' is resolved
- [ ] Coverage for `RegistrarGestionSOS.execute()` > 80% (line coverage)
- [ ] Coverage for `EliminarGestionSOS.execute()` > 90% (line coverage)
