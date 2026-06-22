# Design: Catalog CRUD (Agent, PaymentVia, ClaimKind)

## Technical Approach

Map 3 catalog entities to tables + SQLAlchemy Core repos + in-memory repos following the existing Period pattern exactly. Seed data via Alembic migration with UUID v5 deterministic IDs. Wire real repos in Container (remove stubs). Read-only `/catalogos` UI with 3 tabs. Tests against in-memory repos.

No use case layer — UI reads repos directly (matching the home page pattern). No CRUD forms, no FK constraints.

## Architecture Decisions

| Option | Tradeoff | Decision |
|--------|----------|----------|
| UUID v5 seeds vs auto-increment | Stable IDs across environments; no runtime collision risk | UUID v5 with `uuid.NAMESPACE_DNS + "sos.gestiones"` |
| Read-only UI vs full CRUD | No create/update/delete needed — consumers only lookup by name or ID | Read-only with `ui.table` |
| Repo `get_sos()` / `get_transferencia()` via name lookup | Maps to `get_by_name("SOS")` — simple, no extra columns | Name-based lookup in both repo implementations |
| FK constraints vs no FKs | Codebase convention: no FKs (see payments.payer_id, sos_claims tables) | No FK constraints |
| In-memory repos as test doubles | Isolated, fast, no DB needed for unit tests | 3 in-memory repos matching Period pattern |
| Tabbed UI vs separate pages | All 3 catalogs are tiny; tabs reduce navigation complexity | `ui.tabs` on single `/catalogos` page |

## Data Model

All 3 tables share the same shape — a catalog is just a name:

```
agents:           agent_id (UUID PK), name (str), active (bool), created_at (datetime)
payment_vias:     payment_via_id (UUID PK), name (str), active (bool), created_at (datetime)
claim_kinds:      claim_kind_id (UUID PK), name (str), active (bool), created_at (datetime)
```

Seed data via deterministic UUID v5 (`uuid.uuid5(NAMESPACE_DNS, "sos.gestiones")` as namespace + `"<table>:<name>"` as name):

**agents:** SOS, SM, Asegurado, Prestador, Productor, Externo
**payment_vias:** Transferencia, Nota de Crédito, Efectivo, Cheque, Cta. Cte. Productor
**claim_kinds:** SOS, Tres Arroyos, Especial

## File Changes

| File | Action | Description |
|------|--------|-------------|
| `src/infrastructure/database/tables.py` | Modify | Add `agents`, `payment_vias`, `claim_kinds` table defs |
| `alembic/versions/XXXX_create_catalog_tables.py` | Create | Create 3 tables + INSERT seed data |
| `src/adapters/persistence/sqlalchemy_agent_repository.py` | Create | SQLAlchemy Core repo for Agent |
| `src/adapters/persistence/sqlalchemy_payment_via_repository.py` | Create | SQLAlchemy Core repo for PaymentVia |
| `src/adapters/persistence/sqlalchemy_claim_kind_repository.py` | Create | SQLAlchemy Core repo for ClaimKind |
| `src/adapters/persistence/inmemory_agent_repository.py` | Create | In-memory repo for Agent |
| `src/adapters/persistence/inmemory_payment_via_repository.py` | Create | In-memory repo for PaymentVia |
| `src/adapters/persistence/inmemory_claim_kind_repository.py` | Create | In-memory repo for ClaimKind |
| `src/infrastructure/container.py` | Modify | Builder fns, remove `_StubAgentRepository` + `_StubPaymentViaRepository`, add properties |
| `src/ui/pages/catalogos.py` | Create | `/catalogos` page with `ui.tabs`, 3 `ui.table` |
| `src/ui/components/shell.py` | Modify | Add "Catálogos" nav item with `"list"` icon |
| `main.py` | Modify | Import + register `register_catalogos_page` |
| `tests/test_catalogos.py` | Create | Tests for all 3 in-memory repos |

## Interfaces / Contracts

No new ports — `AgentRepoPort`, `PaymentViaRepoPort`, `ClaimKindRepoPort` already exist in `src/domain/ports/repositories.py`.

Each SQLAlchemy repo follows the exact `_get_conn()` / `_row_to_entity()` / `sa.Table` pattern from `SqlAlchemyPeriodRepository`. Each in-memory repo follows `list[T]` / `next(... for p in ...)` from `InMemoryPeriodRepository`.

Special getters (`get_sos`, `get_transferencia`, etc.) are implemented as:
```python
def get_sos(self) -> Agent | None:
    return self.get_by_name("SOS")
```

## Testing Strategy

| Layer | What to Test | Approach |
|-------|-------------|----------|
| Unit | All 3 in-memory repos: get_by_id, add, get_all, exists, update, delete, get_by_ids, domain methods | Pattern-match `test_periods.py` exactly, one `_seed_*` helper per entity |

No integration tests — SQLAlchemy repos use production code path; migration tested manually via `alembic upgrade head`.

## Migration / Rollout

`alembic upgrade head` applies migration. Seed data inserted atomically in the same transaction. Rollback: `alembic downgrade -1` drops 3 tables, no data loss.

## Key Decisions

1. **UUID v5 seeds** — deterministic across envs, no runtime collision
2. **No FK constraints** — matches codebase convention
3. **Name-based special getters** — avoids schema complexity for 1:1 mapping
4. **Read-only UI** — minimal scope, unblocks payment/claim validation
5. **`_Activatable` methods** — `activate`/`inactivate` delegates to `update` with `active=True/False`

## Affected Areas

| Area | Impact |
|------|--------|
| `tables.py` | +3 table defs (agents, payment_vias, claim_kinds) |
| Alembic | 1 new migration (head: c90154480bf3) |
| Repositories | 3 SQLAlchemy + 3 in-memory = 6 new files |
| Container | +3 builder fns, -2 stubs, +3 properties |
| UI | 1 new page (`/catalogos`), 1 nav link in shell |
| Tests | 1 new test file (~240 lines) |
| `main.py` | 1 import + 1 registration |
