# Proposal: Group Claim Edit

## Intent

Allow agents to change which group a claim belongs to directly from the claim detail page. Today the group field is read-only — agents have no way to correct a wrong group assignment after creation, forcing them to delete and recreate the claim.

## Scope

### In Scope
- Fix `SqlAlchemyClaimRepository.update()` to include `group_id` (latent bug)
- New `ActualizarGrupoDeGestion` use case with group-existence validation and audit
- Wire use case in Container
- Replace read-only "Grupo" field with inline autocomplete dropdown on detail page
- Unit tests for new use case

### Out of Scope
- Full claim edit page (only group field)
- Editing `GroupedClaim.group_claim_id` (separate batch concept)
- Group creation from the detail page (group must exist first)
- FK constraint at DB level (no migration planned)

## Capabilities

### New Capabilities
None

### Modified Capabilities
- `claim-detail`: Add inline group editing — the group field changes from read-only text to an editable autocomplete dropdown. The "Out of Scope (v2+)" section is updated to only exclude non-group field editing.

## Approach

Fix `SqlAlchemyClaimRepository.update()` (add `group_id` to the UPDATE values dict alongside the existing fields). Create `ActualizarGrupoDeGestion(claim_id, new_group_id)` use case: validate claim exists → validate new group exists → update via `UnitOfWork(enable_audit=True)`. Wire in Container. Replace static group text on the detail page with an autocomplete dropdown (reuse the pattern from `gestiones_nueva.py` — search-by-name, select from results).

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `src/adapters/persistence/sqlalchemy_claim_repository.py` | Modified | Add `group_id` to `update()` VALUES dict |
| `src/application/use_cases/claims/actualizar_grupo_de_gestion.py` | New | ActualizarGrupoDeGestion use case |
| `src/infrastructure/container.py` | Modified | Wire new use case |
| `src/ui/pages/gestiones_detalle.py` | Modified | Replace read-only group with autocomplete |
| `tests/test_claims.py` | Modified | Tests for new use case |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| No FK constraint on `claims.group_id` | Low | Use case validates group existence before update |
| Audit diff misses `group_id` changes | Low | Verify `AuditRepositoryWrapper` captures old/new values correctly |
| GroupedClaim batch desync | Low | Acceptable — `Claim.group_id` and `GroupedClaim.group_claim_id` are separate concerns |
| Race condition on concurrent edits | Low | Last-write-wins, acceptable for this app's usage |

## Rollback Plan

1. Revert `sqlalchemy_claim_repository.py` change
2. Delete `actualizar_grupo_de_gestion.py` use case
3. Revert container wiring
4. Revert `gestiones_detalle.py` to read-only group text
5. Remove/add reverted tests

## Dependencies

None

## Success Criteria

- [ ] `SqlAlchemyClaimRepository.update()` successfully persists `group_id` changes
- [ ] Use case raises `ClaimNotFoundError` for invalid claim_id and `ValueError` for invalid group_id
- [ ] Detail page shows autocomplete dropdown and persists new group selection
- [ ] Audit log captures before/after `group_id` values correctly
- [ ] All existing tests pass
