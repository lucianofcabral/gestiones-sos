# Proposal: Catalog CRUD (Agent, PaymentVia, ClaimKind)

## Intent

Unblock payment/claim validation that depends on Agent, PaymentVia, and ClaimKind lookups. Repo ports exist but stubs return `None` — any code path resolving "is this payer SOS?" fails silently. Real repos + seed data + read-only UI are needed.

## Scope

### In Scope
1. `agents`, `payment_vias`, `claim_kinds` tables in `tables.py`
2. Alembic migration: create tables + seed with deterministic UUIDs (6 agents, 5 vias, 3 kinds)
3. 3 SQLAlchemy repos + 3 in-memory repos (matching Period pattern)
4. Container: builder fns, remove `_Stub*`, expose properties
5. `/catalogos` page with 3 tabs (read-only tables)
6. Sidebar nav: add Catálogos link
7. `tests/test_catalogos.py` (in-memory pattern)

### Out of Scope
- CRUD forms, use case layer, HTTP error mapping, FK constraints

## Capabilities

### New
- `catalog-listing`: Read-only list/view at `/catalogos` for Agent, PaymentVia, ClaimKind.

### Modified
- `navigation`: Add `/catalogos` to sidebar.

## Approach

3 tables in `tables.py`. Alembic migration with `op.create_table` + `op.execute` INSERT with UUID v5 seeds. SQLAlchemy repos with `_row_to_model` + `_get_conn`. In-memory repos with `list[T]` store. Container: `_build_*` factories, drop `_Stub*`, wire properties. UI: NiceGUI `ui.table` + `ui.tabs`, direct repo reads.

## Affected Areas

| Area | Impact |
|------|--------|
| `tables.py` | +3 table defs |
| `alembic/versions/` | New migration |
| `sqlalchemy_*_repository.py` x3 | New |
| `inmemory_*_repository.py` x3 | New |
| `container.py` | Builder fns, rm stubs, properties |
| `src/ui/pages/catalogos.py` | New page |
| `shell.py` | +Catálogos nav |
| `tests/test_catalogos.py` | New tests |
| `openspec/specs/catalog-listing/spec.md` | New spec |
| `openspec/specs/navigation/spec.md` | Modified |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| UUID collision with existing data | Low | UUID v5 with namespace |
| Migration conflicts | Low | Point to latest head |

## Rollback Plan

`alembic downgrade -1` drops 3 tables. Revert changed files. No data loss — seed-only tables.

## Dependencies

Current migration head `c90154480bf3`.

## Success Criteria

- [ ] `alembic upgrade head` succeeds with seed data in 3 tables
- [ ] SQLAlchemy repos return seeded rows via `get_all()`
- [ ] In-memory repos pass CRUD tests (add, get_by_id, get_all, exists, update, delete, get_by_ids)
- [ ] Container exposes real `agent_repo`, `payment_via_repo`, `claim_kind_repo`
- [ ] `/catalogos` renders 3 tabs with seed data
- [ ] Sidebar shows Catálogos link → `/catalogos`
