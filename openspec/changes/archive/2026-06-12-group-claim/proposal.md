# Proposal: Group Claim CRUD

## Intent

GroupClaims are a grouping mechanism so multiple claims can "entrar juntos" (come in together on the same invoice) while staying individually registrable. The domain entity and port already exist; this delivers the full implementation stack so users can create and manage groups from the UI.

## Scope

### In Scope
1. `group_claims` table in `tables.py` + Alembic migration
2. `SqlAlchemyGroupClaimRepository` (with JOIN-based `get_by_claim_id`, ILIKE-based `get_by_text_like`)
3. `InMemoryGroupClaimRepository` (with `_DocReachable` stubs)
4. Use cases: `RegistrarGrupo`, `ObtenerGrupos`, `EliminarGrupo`, `ActualizarGrupo`
5. Container wiring: builder fn, repo property, use case properties
6. UI page at `/grupos` (list + create inline form)
7. Sidebar nav: add "Grupos" link
8. `tests/test_grupos.py` (in-memory pattern)

### Out of Scope
- Edit-in-place on the table (use delete + re-create)
- `_Activatable` (GroupClaim has no active flag — simple catalog like ClaimKind but without activation)
- FK constraints to `claims.group_id` (pattern consistency with other catalogs)
- Document entity integration (exists separately via `DocumentTypeEnum.GROUP_CLAIM`)

## Capabilities

### New
- `group-claim-crud`: CRUD at `/grupos` for GroupClaim entities with list and create.

### Modified
- `navigation`: Add `/grupos` to sidebar.

## Approach

Follow `ClaimKind` pattern exactly (simple catalog, no active flag). `group_claims` table: `group_id UUID PK`, `name VARCHAR(100) UNIQUE NOT NULL`, `created_at TIMESTAMP`. SQLAlchemy repo with `_row_to_model` + `_get_conn`. In-memory repo with `list[GroupClaim]` store. Use cases as thin wrappers over repo calls. UI: NiceGUI `ui.table` + `ui.input` + `ui.button` for inline create, repo reads via container. Tests cover BaseRepo + GroupClaimRepoPort methods.

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `tables.py` | Modified | +`group_claims` table def |
| `alembic/versions/` | New | Migration: create `group_claims` |
| `sqlalchemy_group_claim_repository.py` | New | SQLAlchemy impl with JOIN for `get_by_claim_id` |
| `inmemory_group_claim_repository.py` | New | In-memory impl with `_DocReachable` stubs |
| `src/application/use_cases/claims/` | New | registrar_grupo.py, obtener_grupos.py, eliminar_grupo.py, actualizar_grupo.py |
| `container.py` | Modified | Builder fn, repo property, use case properties |
| `src/ui/pages/grupos.py` | New | List + create page |
| `src/ui/components/shell.py` | Modified | Add "Grupos" sidebar link |
| `main.py` | Modified | Register grupo page |
| `tests/test_grupos.py` | New | In-memory tests |
| `openspec/specs/group-claim-crud/spec.md` | New | Capability spec |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Migration conflicts | Low | Point to `c90154480bf3` head |
| Name uniqueness violation | Low | DB UNIQUE constraint + in-memory `exists` check |

## Rollback Plan

`alembic downgrade -1` drops table. Revert changed files in reverse order. No data loss risk — no production data depends on it yet.

## Dependencies

Current migration head `c90154480bf3`. Domain entity `GroupClaim` and port `GroupClaimRepoPort` already exist.

## Success Criteria

- [ ] `alembic upgrade head` creates `group_claims` table
- [ ] SQLAlchemy repo: `add`, `get_by_id`, `get_by_group_name`, `get_by_text_like` (ILIKE), `get_by_claim_id` (JOIN) all work
- [ ] In-memory repo: BaseRepo methods + `get_by_group_name`, `get_by_text_like`, `get_by_claim_id` + `_DocReachable` stubs
- [ ] 4 use cases execute correctly against in-memory repos
- [ ] Container wires repo + use cases
- [ ] `/grupos` renders list with inline create; sidebar links to it
- [ ] `tests/test_grupos.py` passes
