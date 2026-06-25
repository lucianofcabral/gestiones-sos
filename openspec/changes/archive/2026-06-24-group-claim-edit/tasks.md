# Tasks: Group Claim Edit

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | ~175 |
| 400-line budget risk | Low |
| Chained PRs recommended | No |
| Suggested split | Single PR |
| Delivery strategy | auto-forecast |
| Chain strategy | single-pr |

Decision needed before apply: No
Chained PRs recommended: No
Chain strategy: single-pr
400-line budget risk: Low

## Phase 1: Fix Repository Bug

- [x] 1.1 Add `group_id` to `SqlAlchemyClaimRepository.update()` VALUES dict (line 87) alongside existing fields

## Phase 2: Core Use Case + Wiring

- [x] 2.1 Create `ActualizarGrupoDeGestionInput(BaseModel)` with `claim_id: UUID` and `new_group_id: UUID` + `ActualizarGrupoDeGestionOutput(BaseModel)` with `claim_id`, `old_group_id`, `new_group_id`, `group_name`
- [x] 2.2 Create `ActualizarGrupoDeGestion` use case: validate claim exists → validate group exists → update via `uow: UnitOfWork` (with `enable_audit=True`), return output with group_name resolved
- [x] 2.3 Wire `actualizar_grupo_de_gestion` property in container.py (inject `SqlAlchemyUnitOfWork(enable_audit=True)` and `GroupClaimRepoPort`)

## Phase 3: UI Integration

- [x] 3.1 In `gestiones_detalle.py`: replace read-only `_field("Grupo", detalle.group_name)` with `ui.select` using `container.obtener_grupos.execute()`, group name as label + UUID as value, pre-select current group; wire `on_change` → `_on_group_edit` handler that calls use case and reloads page

## Phase 4: Testing

- [x] 4.1 Create `test_actualizar_grupo_de_gestion.py`: `FakeUnitOfWork` + `InMemoryGroupClaimRepository` fixtures; seed claim + group; test happy path (group_id changes, commit succeeds)
- [x] 4.2 Add scenario: claim not found raises `ClaimNotFoundError` (random claim UUID)
- [x] 4.3 Add scenario: group not found raises `ValueError` with Spanish error message

## Phase 5: Spec Maintenance

- [x] 5.1 Update `openspec/changes/group-claim-edit/specs/claim-detail/spec.md` — remove inline group editing from "Out of Scope (v2+)"
