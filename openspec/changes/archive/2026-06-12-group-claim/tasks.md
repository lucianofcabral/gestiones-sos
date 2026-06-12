# Tasks: Group Claim CRUD

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | ~650–800 |
| 400-line budget risk | High |
| Review budget (custom) | 800 lines |
| Chained PRs recommended | No |
| Suggested split | Single PR |
| Delivery strategy | auto-forecast |
| Chain strategy | size-exception |

Decision needed before apply: No
Chained PRs recommended: No
Chain strategy: size-exception
400-line budget risk: High

### Suggested Work Units

| Unit | Goal | Likely PR | Notes |
|------|------|-----------|-------|
| 1 | Full GroupClaim stack — schema → repos → use cases → container → UI → tests | PR 1 | Single PR, same pattern as catalog-crud (exception-ok precedent) |

## Phase 1: DB Schema

- [x] 1.1 Add `group_claims` table def to `src/infrastructure/database/tables.py` (UUID PK, name VARCHAR(100) UNIQUE, created_at — no active flag)
- [x] 1.2 Create `alembic/versions/3a8f9c1e4b6d_create_group_claims_table.py` — `down_revision="27fe323b1ad7"`, create `group_claims` table, downgrade drops it

## Phase 2: Repositories

- [x] 2.1 Create `src/adapters/persistence/sqlalchemy_group_claim_repository.py` — SQLAlchemy Core repo with base CRUD + `get_by_group_name` + `get_by_text_like` (ILIKE) + `get_by_claim_id` (JOIN on `claims.group_id`)
- [x] 2.2 Create `src/adapters/persistence/inmemory_group_claim_repository.py` — `list[GroupClaim]` store with base CRUD + `get_by_group_name` + `get_by_text_like` + `get_by_claim_id` + `_DocReachable` stubs returning `[]`

## Phase 3: Use Cases

- [x] 3.1 Create `src/application/use_cases/claims/registrar_grupo.py` — input: name, output: GroupClaim; return existing if duplicate
- [x] 3.2 Create `src/application/use_cases/claims/obtener_grupos.py` — get_all (ordered by name) or get_by_text_like
- [x] 3.3 Create `src/application/use_cases/claims/eliminar_grupo.py` — input: group_id, no-op if not found
- [x] 3.4 Create `src/application/use_cases/claims/actualizar_grupo.py` — input: group_id + name, returns updated GroupClaim

## Phase 4: Container Wiring

- [x] 4.1 Add `_build_group_claim_repo()` builder fn to `src/infrastructure/container.py`; import `GroupClaimRepoPort` + new SQLAlchemy repo; wire in `__init__`; add property
- [x] 4.2 Wire 4 use cases as properties in container: `registrar_grupo`, `obtener_grupos`, `eliminar_grupo`, `actualizar_grupo`

## Phase 5: UI Page

- [x] 5.1 Create `src/ui/pages/grupos.py` — `/grupos` page with `AppShell`, `ui.table` listing all groups (sorted by name), inline create form with `ui.input` + `ui.button`
- [x] 5.2 Add `("Grupos", "/grupos", "group")` to `AppShell._nav_items()` in `src/ui/components/shell.py`
- [x] 5.3 Import + call `register_grupos_page()` in `main.py`

## Phase 6: Tests

- [x] 6.1 Create `tests/test_grupos.py` — fixture with `InMemoryGroupClaimRepository`; test BaseRepo methods + `get_by_group_name` + `get_by_text_like` + `get_by_claim_id` + `_DocReachable` stubs + 4 use cases (pattern-match `test_catalogos.py`)
