# Design: Group Claim Edit

## Technical Approach

Fix the latent `group_id` omission in `SqlAlchemyClaimRepository.update()`, create a focused `ActualizarGrupoDeGestion` use case with claim+group validation inside UoW+audit, and replace the read-only group text on `/gestiones/{id}` with an inline `ui.select` from existing groups.

## Architecture Decisions

| Decision | Options | Rationale |
|----------|---------|-----------|
| Fix `update()` vs dedicated `update_group()` | (1) Fix `update()` to include `group_id`; (2) Add `update_group()` to protocol | Fix `update()` — matches proposal, fixes a real latent bug, and the protocol already supports it. Adding a new method would require updating the protocol, both impls, and the audit wrapper. |
| `ui.select` vs `ui.input` with autocomplete | (1) `ui.select` with `with_input=True`; (2) `ui.input` with `autocomplete` | **`ui.select`** — only existing groups are valid (no on-the-fly creation from detail page), pre-selection is natural, and the component enforces valid values. Pattern from payment dialogs is well-established. |
| New test file vs extend existing | (1) New `test_actualizar_grupo_de_gestion.py`; (2) Append to `test_claims.py` | **New file** — `test_claims.py` is already 543 lines with 3 use case families. Separate file isolates the changepoint and keeps the review diff clean. |

## Data Flow

```
UI (gestiones_detalle.py)           Container                     Use Case                     UoW / Repos / DB
       │                               │                             │                              │
       │  ui.select('Grupo')           │                             │                              │
       │  on_change → _on_group_edit   │                             │                              │
       │──────────────────────────────>│                             │                              │
       │                               │  actualizar_grupo_de_       │                              │
       │                               │  gestion.execute(inp)       │                              │
       │                               │────────────────────────────>│                              │
       │                               │                             │  claim_repo.get_by_id(claim) │
       │                               │                             │──────────────────────────────>│
       │                               │                             │<─────────── Claim ───────────│
       │                               │                             │                              │
       │                               │                             │  group_claim_repo.           │
       │                               │                             │  get_by_id(new_group_id)     │
       │                               │                             │──────────────────────────────>│
       │                               │                             │<──── GroupClaim or None ─────│
       │                               │                             │                              │
       │                               │                             │  with uow:                   │
       │                               │                             │    uow.claims.update(id,     │
       │                               │                             │      claim.copy(             │
       │                               │                             │        group_id=new_id))     │
       │                               │                             │──────────────────────────────>│
       │                               │                             │           AuditRepo          │
       │                               │                             │      captures old/new vals   │
       │                               │<──────── success ───────────│                              │
       │<─── ui.navigate.reload() ─────│                             │                              │
       │    (page refreshes with       │                             │                              │
       │     new group_name)           │                             │                              │
```

## File Changes

| File | Action | Description |
|------|--------|-------------|
| `src/adapters/persistence/sqlalchemy_claim_repository.py` | Modify | Add `group_id` to `update()` VALUES dict (line 88) |
| `src/application/use_cases/claims/actualizar_grupo_de_gestion.py` | Create | New use case: validate claim + group → update via UoW+audit |
| `src/infrastructure/container.py` | Modify | Wire `_actualizar_grupo_de_gestion` property |
| `src/ui/pages/gestiones_detalle.py` | Modify | Replace `_field("Grupo", ...)` with inline `ui.select` + edit handler |
| `openspec/specs/claim-detail/spec.md` | Modify | Update "Out of Scope (v2+)" — remove inline editing caveat for group |
| `tests/test_actualizar_grupo_de_gestion.py` | Create | Unit tests with in-memory repos + `FakeUnitOfWork` |

## Interfaces / Contracts

```python
# New use case input
class ActualizarGrupoDeGestionInput(BaseModel):
    claim_id: UUID
    new_group_id: UUID

# New use case output
class ActualizarGrupoDeGestionOutput(BaseModel):
    claim_id: UUID
    old_group_id: UUID
    new_group_id: UUID
    group_name: str

# Use case signature
class ActualizarGrupoDeGestion:
    def __init__(self, uow: UnitOfWork, group_claim_repo: GroupClaimRepoPort) -> None: ...
    def execute(self, input_data: ActualizarGrupoDeGestionInput) -> ActualizarGrupoDeGestionOutput: ...
```

## Testing Strategy

| Layer | What to Test | Approach |
|-------|-------------|----------|
| Unit | Happy path — valid claim + valid group | In-memory repos, seed claim + group, call use case, verify `claim.group_id` changed |
| Unit | Claim not found raises `ClaimNotFoundError` | Random UUID for claim, expect typed exception |
| Unit | Group not found raises `ValueError` | Valid claim + random group UUID, expect `ValueError` with Spanish message |
| Unit | UoW commit is called on success | Verify `FakeUnitOfWork.commit()` is reachable (no exception in `__exit__`) |
| Integration | SQLAlchemy `update()` persists `group_id` | (Manual / trust in test pattern — in-memory tests cover the logic) |

## Migration / Rollout

No migration required. The `group_id` column already exists on `claims` table — the bug is only in the UPDATE statement.

## Open Questions

- [ ] Should the audit diff for `group_id` show the old group name and new group name (vs raw UUIDs)? The current `AuditRepositoryWrapper` captures raw values — name resolution is a UX concern for the audit viewer, not the writer.
