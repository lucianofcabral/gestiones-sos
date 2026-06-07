# Proposal: Fix EliminarGestionSOS — Replace copy-paste bug with proper soft-delete

## Intent

`src/application/use_cases/claims/eliminar_gestion_sos.py` is a verbatim copy of `registrar_gestion_sos.py` — same class names (`RegistrarGestionSOSInput`, `RegistrarGestionSOSOutput`, `RegistrarGestionSOS`), same creation logic. Delete functionality is completely broken. This replaces it with a correct soft-delete use case.

## Scope

### In Scope
- Rewrite `EliminarGestionSOS` use case with proper DTOs and soft-delete logic via `ClaimRepoPort.inactivate()`
- Wire the use case in the DI Container
- Add unit tests using `InMemoryClaimRepository`

### Out of Scope
- Physical DELETE from DB (soft delete only)
- Cascading deactivation of associated `SosClaim` entities
- Payment guard (no payments module exists yet — deferred)
- UI changes or API endpoints
- State-based deletion restrictions
- Domain-specific exception types (keep `ValueError` for now)

## Capabilities

### New Capabilities
- `claim-deletion`: Soft-delete of Claim entities via `active=False` — idempotent, authorization-free, no cascade

### Modified Capabilities
None — no existing specs to modify.

## Approach

1. **Rewrite `eliminar_gestion_sos.py`**: Replace the RegistrarGestionSOS copy with `EliminarGestionSOSInput` (containing `claim_id: UUID`), `EliminarGestionSOSOutput` (containing `claim_id: UUID`, `success: bool`), and the `EliminarGestionSOS` use case. The use case injects `ClaimRepoPort`, looks up the claim, raises `ValueError` if not found, calls `claim_repo.inactivate(claim_id)`, and returns success.
2. **Update Container**: Add `PostgreSQLClaimRepository` and `EliminarGestionSOS` as properties, following the existing pattern.
3. **Add tests**: Create `tests/test_claims.py` with scenarios: happy path, non-existent claim, idempotent re-deletion.

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `src/application/use_cases/claims/eliminar_gestion_sos.py` | Rewrite | Replace copy-paste with real soft-delete use case |
| `src/infrastructure/container.py` | Modified | Wire claim repo and `EliminarGestionSOS` |
| `tests/test_claims.py` | New | Unit tests with in-memory repo |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| SosClaim records become orphaned after claim deactivation | Low (by design) | Business rule: SosClaims stay active and owned to the claim |
| Claim not found returns generic ValueError | Low | Matches existing codebase convention |

## Rollback Plan

Revert the three affected files. Tests will fail after revert, confirming the fix.

## Dependencies

- `Claim` entity already has `active` field ✓
- `ClaimRepoPort` already has `inactivate()` ✓
- `InMemoryClaimRepository` already implements `inactivate()` ✓

## Success Criteria

- [ ] Existing auth tests still pass
- [ ] New claims tests pass (happy path, not found, idempotent)
- [ ] `EliminarGestionSOS` sets `active=False` on the Claim (verified via in-memory repo read-back)
- [ ] `SosClaim` records remain active after claim deletion

### Proposal question round

This proposal was shaped by direct conversation with the user. No further questions needed.
