# Design: Group Claim CRUD

## Technical Approach

Follow the `ClaimKind` pattern (simple catalog, no active flag) with one structural difference: `GroupClaimRepoPort` extends `_DocReachable` and defines three custom lookups (`get_by_claim_id`, `get_by_group_name`, `get_by_text_like`). Data flows: UI → use case → repo → DB (SQLAlchemy Core, no ORM). In-memory repo for tests.

**Correction to proposal**: migration `down_revision` must point to `27fe323b1ad7`, not `c90154480bf3` — the documents migration (`27fe323b1ad7`) is the actual head, sitting one revision above `9f7c7e3b1a5d` which already depends on `c90154480bf3`.

## Architecture Decisions

| Option | Tradeoffs | Decision |
|--------|-----------|----------|
| Table PK as `group_id UUID` | Consistent with every other table; no natural PK for groups | Use UUID PK, same pattern |
| `name VARCHAR(100) UNIQUE NOT NULL` | Matches catalog tables; no `active` column for GroupClaim | UNIQUE constraint; omit `active` as specified |
| `get_by_claim_id`: JOIN `claims.group_id` | Requires `claims` table import in SQLAlchemy repo; in-memory iterates claim store | Both repos import the `claims` table/entity; in-memory stores `(claim_id, group_id)` pairs or iterates the claim store |
| In-memory `_DocReachable` stubs | Returns `[]` for now, same pattern as `InMemoryClaimRepository` | Follow existing convention — stub returns empty list |
| Use cases as thin wrappers | No business logic in GroupClaim CRUD; matches ClaimKind pattern | One file per use case (register, list, delete, update) |

## Data Flow

```
/grupos (UI) ──→ RegistrarGrupo ──→ SqlAlchemyGroupClaimRepo.add()
                ──→ ObtenerGrupos  ──→ repo.get_all()
                ──→ EliminarGrupo  ──→ repo.delete(id)
                ──→ ActualizarGrupo──→ repo.update(id, model)

get_by_claim_id:
    claim_id → repo → JOIN claims ON claims.group_id = group_claims.group_id → GroupClaim

get_by_text_like:
    text → repo → ILIKE on group_claims.name → list[GroupClaim]
```

## File Changes

| File | Action | Description |
|------|--------|-------------|
| `src/infrastructure/database/tables.py` | Modify | Add `group_claims` table def |
| `alembic/versions/xxxxxxxxxxxx_create_group_claims_table.py` | New | Migration: `down_revision="27fe323b1ad7"`, create `group_claims` |
| `src/adapters/persistence/sqlalchemy_group_claim_repository.py` | New | SQLAlchemy Core repo; JOIN for `get_by_claim_id`, ILIKE for `get_by_text_like` |
| `src/adapters/persistence/inmemory_group_claim_repository.py` | New | List store; `_DocReachable` stubs return `[]` |
| `src/application/use_cases/claims/registrar_grupo.py` | New | Input: name; output: GroupClaim |
| `src/application/use_cases/claims/obtener_grupos.py` | New | Input: none (get_all) or text (get_by_text_like) |
| `src/application/use_cases/claims/eliminar_grupo.py` | New | Input: group_id; output: success |
| `src/application/use_cases/claims/actualizar_grupo.py` | New | Input: group_id + name; output: updated GroupClaim |
| `src/infrastructure/container.py` | Modify | Add `_build_group_claim_repo()`, `__init__` wiring, properties |
| `src/ui/pages/grupos.py` | New | List table + inline create form at `/grupos` |
| `src/ui/components/shell.py` | Modify | Add `("Grupos", "/grupos", "group")` to `_nav_items()` |
| `main.py` | Modify | Import + call `register_grupos_page()` |
| `tests/test_grupos.py` | New | In-memory pattern; BaseRepo + GroupClaimRepoPort + use case tests |

## Interfaces / Contracts

### `group_claims` table

```python
group_claims = sa.Table(
    "group_claims",
    metadata,
    sa.Column("group_id", sa.UUID, primary_key=True),
    sa.Column("name", sa.String(100), nullable=False, unique=True),
    sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
)
```

### SQLAlchemy repo — key custom methods

```python
def get_by_claim_id(self, claim_id: UUID) -> GroupClaim | None:
    with self._get_conn() as conn:
        row = conn.execute(
            sa.select(group_claims)
            .select_from(group_claims.join(claims, claims.c.group_id == group_claims.c.group_id))
            .where(claims.c.claim_id == claim_id)
        ).fetchone()
    return self._row_to_entity(row) if row else None

def get_by_text_like(self, text: str) -> list[GroupClaim]:
    with self._get_conn() as conn:
        rows = conn.execute(
            sa.select(group_claims).where(group_claims.c.name.ilike(f"%{text}%"))
        ).fetchall()
    return [self._row_to_entity(r) for r in rows]
```

### In-memory repo — key custom methods

```python
def get_by_claim_id(self, claim_id: UUID) -> GroupClaim | None:
    return next(
        (g for g in self._store if g.group_id in
         [c.group_id for c in self._claim_store if c.claim_id == claim_id]),
        None
    )
# _DocReachable: get_by_document_id → [], get_by_document → []
```

## Testing Strategy

| Layer | What to Test | Approach |
|-------|-------------|----------|
| In-memory repo | BaseRepo methods (add, get_by_id, get_all, delete, update, exists, get_by_ids) | `test_grupos.py`, fixture creates `InMemoryGroupClaimRepository` |
| In-memory repo | `get_by_group_name`, `get_by_text_like`, `get_by_claim_id`, `_DocReachable` stubs | Seed test data, assert correct filtering |
| Use cases | RegistrarGrupo (duplicate name→error), ObtenerGrupos (all/like), EliminarGrupo (found/not-found), ActualizarGrupo | Use in-memory repo as injected dependency |

## Migration / Rollout

`alembic upgrade head` creates `group_claims` table. Rollback: `alembic downgrade -1`. No data migration needed — table is new, no production data depends on it.

## Open Questions

- [ ] `get_by_claim_id` port returns `GroupClaim` (singular) — confirm business rule: a claim belongs to exactly one group (yes, `claims.group_id` is a single FK)
- [ ] Register page positioning in `main.py` — alphabetical or group with other `/claims` pages?
