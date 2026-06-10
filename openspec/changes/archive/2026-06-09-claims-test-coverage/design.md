# Design: Claims Test Coverage

## Technical Approach

Add an `InMemorySosClaimRepository` fake and a `FakeUnitOfWork` to enable unit testing `RegistrarGestionSOS` (zero tests today). Append tests to `tests/test_claims.py` following the established in-memory-fake pattern from `test_auth.py` and `test_payments.py`. No production code changes — both use cases already use constructor DI.

## Architecture Decisions

| Decision | Choice | Alternatives | Rationale |
|----------|--------|-------------|-----------|
| InMemorySosClaimRepository location | `src/adapters/persistence/inmemory_sos_claim_repository.py` | Inline in test file | Consistency with `InMemoryClaimRepository`, `InMemoryPaymentRepository`; keeps fakes alongside their protocol |
| FakeUnitOfWork implementation | Subclass `UnitOfWork` ABC in `tests/test_claims.py` | Separate module, adapter dir | Only used in one test file; matches `FakePasswordPort` inline pattern from `test_auth.py` |
| FakeUnitOfWork strategy | Wraps `InMemoryClaimRepository` + `InMemorySosClaimRepository`; no-op commit/rollback | Full transaction simulation | In-memory repos are self-contained; transaction isolation is tested via integration tests |
| EliminarGestionSOS gap tests | None needed — all 5 spec scenarios covered by existing tests | Add explicit gap tests | `test_delete_existing_claim_sets_active_false` already covers backward compat (no `payment_repo`) AND no-payments scenario |
| PYTHONPATH fix | No code change — `pyproject.toml` already has `pythonpath = ["."]` | Edit pyproject.toml | `ModuleNotFoundError` is a local env/install issue; needs `uv sync` or `uv run` |

## Existing Coverage Analysis (EliminarGestionSOS)

| Scenario | Test File | Covered |
|----------|-----------|---------|
| Claim not found → ValueError | `test_claims.py` | ✅ |
| Existing claim → active=False | `test_claims.py` | ✅ (no payment_repo = backward compat) |
| Idempotent (double delete) | `test_claims.py` | ✅ |
| Active payments block deletion | `test_payments.py` | ✅ |
| Inactive payments allow deletion | `test_payments.py` | ✅ |

All `claim-deletion/spec.md` requirements are already verified. No additional `EliminarGestionSOS` tests required.

## Data Flow

### RegistrarGestionSOS — Happy Path
```
Test Input ──→ RegistrarGestionSOS.execute(uow)
                    │
                    ├── uow.sos_claims.get_by_number(gestion) → None
                    ├── uow.claims.add(Claim) → claim w/ ID
                    ├── uow.sos_claims.add(SosClaim) → sos_claim w/ ID
                    │
                    └── Returns RegistrarGestionSOSOutput
                              → assert output DTO fields
                              → assert claim + sos_claim in repos (read-back)
```

### RegistrarGestionSOS — Duplicate Gestion
```
Test Input (gestion=N) ──→ RegistrarGestionSOS.execute(uow)
                              │
                              ├── uow.sos_claims.add(SosClaim(gestion=N))  # seed
                              ├── uow.sos_claims.get_by_number(N) → SosClaim
                              └── Raises ValueError("Ya existe una gestión...")
```

## File Changes

| File | Action | Description |
|------|--------|-------------|
| `src/adapters/persistence/inmemory_sos_claim_repository.py` | **Create** | `SosClaimRepoPort` in-memory fake: `BaseRepo` + `_Activatable` + `get_by_number()`, `get_claims_by_claim_id()`, `get_by_status()`, `get_by_text_like()` |
| `tests/test_claims.py` | **Modify** | Add `InMemorySosClaimRepository` fixture, `FakeUnitOfWork` class/fixture, 3 `RegistrarGestionSOS` tests, seed helpers |

## Interfaces / Contracts

### InMemorySosClaimRepository
```python
class InMemorySosClaimRepository:
    # BaseRepo[SosClaim]: add, get_by_id, delete, update, get_all, exists, get_by_ids
    # _Activatable[SosClaim]: activate, inactivate
    def get_by_number(self, claim_number: int) -> SosClaim | None: ...
    def get_claims_by_claim_id(self, claim_id: UUID) -> list[SosClaim]: ...
    def get_by_status(self, status: str) -> list[SosClaim]: ...
    def get_by_text_like(self, text: str) -> SosClaim | None: ...
```

### FakeUnitOfWork
```python
class FakeUnitOfWork(UnitOfWork):
    def __init__(self, claims, sos_claims):
        self.claims = claims
        self.sos_claims = sos_claims
    def commit(self) -> None: pass
    def rollback(self) -> None: pass
    # __enter__ / __exit__ inherited from UnitOfWork ABC
```

## Testing Strategy

| Test | Scenario | Assertions |
|------|----------|-----------|
| `test_registrar_gestion_sos_happy` | Valid input | Output has `claim_id`, `sos_claim_id`; read-back verifies both entities in repos |
| `test_registrar_duplicate_gestion_raises` | Same gestion N twice | `pytest.raises(ValueError, match="Ya existe una gestión")` |
| `test_registrar_field_roundtrip` | All input fields populated | Output DTO fields equal input values (gestion, claimer_name, policy_number, plate) |

## Migration / Rollback

No migration required. All changes are additive (new files, new tests). Rollback: `git revert HEAD`.

## Open Questions

None. All technical decisions resolved by existing project patterns.
