# Design: Periods CRUD

## Technical Approach

Mirror the Grupo CRUD pattern (create-list-delete via inline UI). Add a `UniqueConstraint('year', 'month')` migration, three use cases in `src/application/use_cases/periods/`, a wire-up in the container, and replace the placeholder page at `/periodos`. `EliminarPeriodo` checks `billing_repo.get_by_period_id` and `nc_payment_repo.get_by_period_id` for referential integrity (same app-level pattern as `EliminarFactura`).

## Data Flow

```
/periodos (UI) ──→ CrearPeriodo    ──→ period_repo.get_by_year_month() guard → period_repo.add()
                  → ListarPeriodos  ──→ period_repo.get_n_last(None)
                  → EliminarPeriodo ──→ billing_repo.get_by_period_id() / nc_payment_repo.get_by_period_id() guard → period_repo.delete()
```

## Architecture Decisions

| Option | Tradeoffs | Decision |
|--------|-----------|----------|
| Use case Input/Output pattern | Inner Pydantic models vs flat params | **Inner models** — consistent with `RegistrarFactura`, `RegistrarPago` |
| Delete integrity | DB-level FK restrict vs app-level check | **App-level** — consistent with `EliminarGrupo` / `EliminarFactura`, gives descriptive Spanish errors |
| Migration target | `27701ff330c2` (current head) vs new branch | **`27701ff330c2`** — head hasn't moved, no conflicts |
| Nombre de meses in UI | Hardcode 1-12 map vs import from domain | **Hardcode in page** — `_MESES_ES` is private to entities.py; UI already uses its own mapping |

## Domain Changes

None. `Period` entity already has `year`, `month`, `period_name`, `period_number`.

## File Changes

| File | Action | Description |
|------|--------|-------------|
| `alembic/versions/xxxxxxxxxxxx_add_unique_constraint_periods.py` | New | Migration: `op.create_unique_constraint('uq_periods_year_month', 'periods', ['year', 'month'])`, down_revision=`27701ff330c2` |
| `src/infrastructure/database/tables.py` | Modify | Add `sa.UniqueConstraint('year', 'month', name='uq_periods_year_month')` to `periods` table |
| `src/application/use_cases/periods/crear_periodo.py` | New | `CrearPeriodo.Input(year, month)` → `get_by_year_month` guard → `period_repo.add()` |
| `src/application/use_cases/periods/listar_periodos.py` | New | `ListarPeriodos` → `get_n_last(None)` |
| `src/application/use_cases/periods/eliminar_periodo.py` | New | `EliminarPeriodo.Input(period_id)` → billing+nc checks → `period_repo.delete()` |
| `src/infrastructure/container.py` | Modify | Import + instantiate 3 use cases; expose as properties |
| `src/ui/pages/periodos.py` | Modify | Replace placeholder with create form + period list + delete buttons |
| `tests/test_periods_use_cases.py` | New | Use case tests with in-memory repos |

## Interfaces / Contracts

### Use cases

```python
class CrearPeriodo:
    class Input(BaseModel):
        year: int = Field(ge=2020, lt=2040)
        month: int = Field(ge=1, le=12)
    class Output(BaseModel):
        period: Period
    def execute(self, input: Input) -> Output: ...

class ListarPeriodos:
    class Output(BaseModel):
        periods: list[Period]
    def execute(self) -> Output: ...

class EliminarPeriodo:
    class Input(BaseModel):
        period_id: UUID
    class Output(BaseModel):
        deleted: bool
    def execute(self, input: Input) -> Output: ...
```

### Integrity guard pattern (`EliminarPeriodo`)

```python
def execute(self, input: Input) -> Output:
    period = self._period_repo.get_by_id(input.period_id)
    if period is None:
        return Output(deleted=False)
    invoices = self._billing_repo.get_by_period_id(input.period_id)
    if invoices:
        raise ValueError("No se puede eliminar: el período tiene facturas asociadas")
    ncs = self._nc_payment_repo.get_by_period_id(input.period_id)
    if ncs:
        raise ValueError("No se puede eliminar: el período tiene notas de crédito asociadas")
    self._period_repo.delete(input.period_id)
    return Output(deleted=True)
```

## Testing Strategy

| Layer | What to Test | Approach |
|-------|-------------|----------|
| Use cases | CrearPeriodo (success + duplicate), ListarPeriodos (all periods), EliminarPeriodo (success + billing guard + nc guard + not found) | In-memory period/billing/nc-payment repos as injected deps |

## Migration / Rollout

`alembic upgrade head` adds unique constraint. Rollback: `alembic downgrade -1` drops it. Constraint-only migration — no data changes. Revert files in reverse order.

## Open Questions

None.
