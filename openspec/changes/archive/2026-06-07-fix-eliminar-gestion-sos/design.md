# Design: Fix EliminarGestionSOS — Replace copy-paste bug with proper soft-delete

## Technical Approach

Rewrite `eliminar_gestion_sos.py` from a verbatim copy of `RegistrarGestionSOS` to a standalone soft-delete use case. It will look up the `Claim` by ID, call the already-existing `ClaimRepoPort.inactivate()` to set `active=False`, and return a confirmation DTO. No cascade to `SosClaim`. No payment guard (deferred).

The existing infrastructure — `ClaimRepoPort.inactivate()`, `PostgreSQLClaimRepository.inactivate()`, `InMemoryClaimRepository.inactivate()` — is already implemented and working. The use case is the only missing piece.

## Architecture Decisions

| Option | Tradeoffs | Decision |
|--------|-----------|----------|
| Soft delete via `inactivate()` vs physical `delete()` | Soft delete preserves referential integrity for SosClaims; matches existing pattern (`_Activatable` protocol). | **Soft delete** — `ClaimRepoPort.inactivate()` |
| `ValueError` vs custom `ClaimNotFoundError` | Custom exception is cleaner but adds a new type for a single use case; rest of codebase uses `ValueError` for business errors. | **`ValueError`** — matches existing convention |
| Inject `ClaimRepoPort` vs `UnitOfWork` | UoW is used for transactional writes (RegistrarGestionSOS). This use case is a single-repo, single-operation write — no coordination needed. Direct repo injection is simpler and matches the existing `Me(Login`, `Logout(Login` pattern. | **Direct `ClaimRepoPort` injection** |
| Validate `active=False` before calling `inactivate()` | Unnecessary — `inactivate()` is idempotent. Calling it on an already-inactive claim is a no-op that still returns `True`. | **No pre-check** — let the repo handle it |

## Data Flow

```
Client code
  │
  ▼
EliminarGestionSOS.execute(input)
  │
  ├─ 1. claim = claim_repo.get_by_id(input.claim_id)
  │     └─ if None → raise ValueError("Claim not found")
  │
  ├─ 2. success = claim_repo.inactivate(input.claim_id)
  │     └─ UPDATE claims SET active=false WHERE claim_id=?
  │
  └─ 3. return EliminarGestionSOSOutput(claim_id, success=True)
```

No SosClaim is read or modified. No other entity is touched.

## File Changes

| File | Action | Description |
|------|--------|-------------|
| `src/application/use_cases/claims/eliminar_gestion_sos.py` | Rewrite | Replace copy-paste with `EliminarGestionSOSInput`, `EliminarGestionSOSOutput`, `EliminarGestionSOS` |
| `src/infrastructure/container.py` | Modify | Wire `PostgreSQLClaimRepository` and `EliminarGestionSOS` |
| `tests/test_claims.py` | Create | Unit tests with `InMemoryClaimRepository` |

## Interfaces / Contracts

```python
# Input DTO
class EliminarGestionSOSInput(BaseModel):
    claim_id: UUID

# Output DTO
class EliminarGestionSOSOutput(BaseModel):
    claim_id: UUID
    success: bool

# Use case
class EliminarGestionSOS:
    def __init__(self, claim_repo: ClaimRepoPort): ...

    def execute(self, input_data: EliminarGestionSOSInput) -> EliminarGestionSOSOutput: ...
```

The use case depends only on `ClaimRepoPort` (already exists at `src/domain/ports/repositories.py:84`). No new ports or adapters needed.

## Testing Strategy

| Layer | What to Test | Approach |
|-------|-------------|----------|
| Unit | Happy path — claim exists → `active=False` | Create a claim, run `EliminarGestionSOS.execute()`, read back and assert `claim.active is False` |
| Unit | Not found — claim does not exist → `ValueError` | Call with random UUID, assert `pytest.raises(ValueError, match="not found")` |
| Unit | Idempotent — delete twice → both succeed | Delete, then delete again, both return `success=True` |

Test infrastructure: `InMemoryClaimRepository` (already exists), no fakes needed.

## Migration / Rollout

No migration required. The bug only affects the in-memory code path — no production data is corrupted. The `active` column already exists in the `claims` table.

## Open Questions

None.
