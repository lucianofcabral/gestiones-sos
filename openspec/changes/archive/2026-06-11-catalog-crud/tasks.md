# Tasks: Catalog CRUD (Agent, PaymentVia, ClaimKind)

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | ~700–850 |
| 400-line budget risk | High |
| Chained PRs recommended | No |
| Suggested split | Single PR |
| Delivery strategy | exception-ok |
| Chain strategy | pending |

Decision needed before apply: No
Chained PRs recommended: No
Chain strategy: size-exception
400-line budget risk: High

## Phase 1: DB Schema

- [x] 1.1 Add `agents`, `payment_vias`, `claim_kinds` table defs to `src/infrastructure/database/tables.py` (3 × ~24 lines, same pattern as `periods`)
- [x] 1.2 Create `alembic/versions/9f7c7e3b1a5d_create_catalog_tables.py` — create 3 tables + INSERT seed data (UUID v5) for 6 agents, 5 payment vias, 3 claim kinds

## Phase 2: SQLAlchemy Repos

- [x] 2.1 Create `src/adapters/persistence/sqlalchemy_agent_repository.py` — SQLAlchemy Core repo with base CRUD + `get_by_name` + 4 named getters (`get_sos`, `get_sm`, `get_prestador`, `get_asegurado`) + `activate`/`inactivate`
- [x] 2.2 Create `src/adapters/persistence/sqlalchemy_payment_via_repository.py` — SQLAlchemy Core repo with base CRUD + `get_by_name` + 2 named getters (`get_transferencia`, `get_nc`) + `activate`/`inactivate`
- [x] 2.3 Create `src/adapters/persistence/sqlalchemy_claim_kind_repository.py` — SQLAlchemy Core repo with base CRUD + `get_by_name` + `activate`/`inactivate`

## Phase 3: In-Memory Repos

- [x] 3.1 Create `src/adapters/persistence/inmemory_agent_repository.py` — in-memory `list[Agent]` store, all base methods + domain getters + `activate`/`inactivate`
- [x] 3.2 Create `src/adapters/persistence/inmemory_payment_via_repository.py` — in-memory `list[PaymentVia]` store, all base methods + domain getters + `activate`/`inactivate`
- [x] 3.3 Create `src/adapters/persistence/inmemory_claim_kind_repository.py` — in-memory `list[ClaimKind]` store, all base methods + `get_by_name` + `activate`/`inactivate`

## Phase 4: Container Wiring

- [x] 4.1 Add 3 builder fns (`_build_agent_repo`, `_build_payment_via_repo`, `_build_claim_kind_repo`) to `src/infrastructure/container.py`
- [x] 4.2 Remove `_StubAgentRepository` and `_StubPaymentViaRepository` classes; wire real repos in `__init__`; add 3 properties; import new SQLAlchemy repos + `ClaimKindRepoPort`

## Phase 5: UI Page

- [x] 5.1 Create `src/ui/pages/catalogos.py` — `/catalogos` page with `AppShell`, 3 `ui.tabs`, 3 `ui.table` reading from `get_container()` repos
- [x] 5.2 Add `("Catálogos", "/catalogos", "list")` to `AppShell._nav_items()` in `src/ui/components/shell.py`
- [x] 5.3 Import + call `register_catalogos_page()` in `main.py`

## Phase 6: Tests

- [x] 6.1 Create `tests/test_catalogos.py` — 3 `_seed_*` helpers + per-repo test classes for base CRUD + `activate`/`inactivate` + domain-specific getters (pattern-match `test_periods.py`)
