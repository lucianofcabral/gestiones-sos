# Proposal: Periods — Persistence Layer

## Intent

Period entity and `PeriodRepoPort` already exist in the domain layer, but there is no way to store or retrieve periods. This change adds the missing infrastructure (table, migration, SQLAlchemy repository, in-memory repository, container wiring, and tests) so that periods can be persisted and queried by downstream modules — starting with `payments-module`, which needs Periods for the NcPayment → Period → Invoice chain.

## Scope

### In Scope
- `periods` table definition in SQLAlchemy Core (`tables.py`) — UUID PK, year, month, created_at
- Alembic migration to create the periods table
- `SqlAlchemyPeriodRepository` implementing `PeriodRepoPort` (with `_get_conn` UoW pattern)
- `InMemoryPeriodRepository` for unit testing
- Container wiring for `PeriodRepoPort`
- Unit tests covering all `BaseRepo[Period]` methods + `get_by_year_month` / `get_n_last`

### Out of Scope
- `get_total_billing_by_year_month` implementation — depends on Invoice module (not built), left as `raise NotImplementedError`
- Invoice or Billing modules
- `payments-module` integration
- No soft-delete, no active field — Period is not activatable (a year+month either exists or not)

## Capabilities

### New Capabilities
None — pure infrastructure change. The domain contract (entity + port) already exists. No new business behavior is introduced.

### Modified Capabilities
None

## Approach

Mirror existing `SqlAlchemyClaimRepository` / `InMemoryClaimRepository` pattern:
1. Add `periods` `sa.Table` in `tables.py`
2. Generate Alembic migration following existing style
3. Implement `SqlAlchemyPeriodRepository` with `_get_conn`, `_row_to_period` helper, all `BaseRepo[Period]` methods, `get_by_year_month`, and `get_n_last` (sorted by year DESC, month DESC)
4. Implement `InMemoryPeriodRepository` using `list[Period]`
5. Wire `PeriodRepoPort` → `SqlAlchemyPeriodRepository` in Container
6. Write tests with in-memory repo covering CRUD, edge cases, and custom methods

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `src/infrastructure/database/tables.py` | New table | Add `periods` table |
| `alembic/versions/` | New file | Migration creating periods table |
| `src/adapters/persistence/sqlalchemy_period_repository.py` | New file | SQLAlchemy PeriodRepoPort impl |
| `src/adapters/persistence/inmemory_period_repository.py` | New file | In-memory PeriodRepoPort impl |
| `src/infrastructure/container.py` | Modified | Wire PeriodRepoPort |
| `tests/test_periods.py` | New file | Unit tests |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Column/type mismatch with entity fields | Low | Mirror entity field names and types exactly |
| Migration chain broken by new revision | Low | Run `alembic heads` before generating; target `a56d9e223076` as parent |

## Rollback Plan

1. `alembic downgrade -1` to revert the migration
2. Remove `_build_period_repo` and container wiring
3. Delete the three new source files and the test file

## Dependencies

None. Domain layer (entity + port) already exists.

## Success Criteria

- [ ] `alembic upgrade head` creates the periods table without error
- [ ] `alembic downgrade -1` drops it cleanly
- [ ] All tests in `tests/test_periods.py` pass
- [ ] Container resolves `PeriodRepoPort` without error
- [ ] `get_total_billing_by_year_month` raises `NotImplementedError`
