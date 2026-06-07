# Tasks: Periods — Persistence Layer

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | ~120–160 |
| 400-line budget risk | Low |
| Chained PRs recommended | No |
| Suggested split | Single PR |
| Delivery strategy | single-pr |
| Chain strategy | size-exception |

Decision needed before apply: No
Chained PRs recommended: No
Chain strategy: size-exception
400-line budget risk: Low

### Suggested Work Units

| Unit | Goal | PR | Notes |
|------|------|----|-------|
| 1 | Period persistence (table + repos + wiring + tests) | Single PR | All in one, ~120–160 lines |

## Phase 1: RED — Test file first

- [x] 1.1 Write `tests/test_periods.py` — unit tests for all PeriodRepoPort methods using InMemoryPeriodRepository (imports won't resolve yet = RED)

## Phase 2: GREEN — Make tests pass

- [x] 2.1 Create `src/adapters/persistence/inmemory_period_repository.py` — in-memory `list[Period]` with all `BaseRepo[Period]` + `get_by_year_month`, `get_n_last`, `get_total_billing_by_year_month` (raises `NotImplementedError`)

## Phase 3: Production implementation

- [x] 3.1 Add `periods` table definition in `src/infrastructure/database/tables.py`
- [x] 3.2 Create Alembic migration — new revision targeting `f9f4ceceb489` as parent, creating `periods` table
- [x] 3.3 Create `src/adapters/persistence/sqlalchemy_period_repository.py` — implements all `PeriodRepoPort` methods with `_get_conn` UoW pattern
- [x] 3.4 Wire `PeriodRepoPort` in `src/infrastructure/container.py` — add `_build_period_repo` factory + `period_repo` property

## Phase 4: REFACTOR — Verify

- [x] 4.1 Run `uv run pytest tests/test_periods.py` — all green
- [x] 4.2 Run `alembic upgrade head` and `alembic downgrade -1` — migration works both ways
