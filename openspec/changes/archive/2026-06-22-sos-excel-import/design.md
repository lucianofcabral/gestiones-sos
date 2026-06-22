# Design: SOS Excel Import

## Technical Approach

Standalone import pipeline: an Excel parser (pure function, no infra deps) reads `.xlsx` bytes into structured rows, then a new use case upserts each row in its own UoW transaction. Row-level try/except isolates failures. The UI follows the existing page pattern — `ui.upload()`, preview table, import button, result table. No changes to the existing `RegistrarGestionSOS` use case.

## Architecture Decisions

### Decision: Excel parser as stateless module in `application/services/`

| Option | Tradeoff | Decision |
|--------|----------|----------|
| **Pure function in `services/`** | No infra coupling, trivial to unit-test | ✅ Chosen |
| Inline parser in use case | Harder to test, mixes concerns | Rejected |
| Parser in `adapters/` (infra) | Would couple use case to infra via import | Rejected |

**Rationale**: The parser only needs file bytes + config (sheet name). No database, no DI. Putting it in `application/services/` keeps it in the domain layer while keeping the use case focused on orchestration. `openpyxl` is already a project dependency.

### Decision: UoW class injected as factory for per-row transactions

| Option | Tradeoff | Decision |
|--------|----------|----------|
| **Inject `uow_cls: type[UnitOfWork]`** | Each row gets a fresh transaction; failure is isolated | ✅ Chosen |
| Single UoW for all rows | One failure rolls back everything | Rejected |
| Savepoints on single UoW | DB-specific, adds complexity | Rejected |

**Rationale**: Per spec — each row is independent. Passing the class (not instance) lets the use case create `with uow_cls() as uow:` per row. The existing `SqlAlchemyUnitOfWork` already supports this pattern via `__enter__`/`__exit__`.

### Decision: Claim kind and group resolved once at start

| Option | Tradeoff | Decision |
|--------|----------|----------|
| **Pre-lookup before row loop** | Fail fast if misconfigured, single query | ✅ Chosen |
| Per-row lookup | Unnecessary N+1 queries | Rejected |
| Resolved by caller and passed in | Shifts responsibility to UI layer | Rejected |

**Rationale**: `ClaimKindRepoPort.get_by_name("SOS")` and group lookup are stable for the entire import. Fail early before processing any rows.

### Decision: `/gestiones/importar` as separate page with nav link

| Option | Tradeoff | Decision |
|--------|----------|----------|
| **Separate page + sidebar link** | Distinct workflow, clear UX | ✅ Chosen |
| Inline in `/gestiones` | Crowded, different concerns | Rejected |
| Hidden page (no nav) | Discoverability problem | Rejected |

**Rationale**: Bulk import is a fundamentally different interaction (file upload → preview → confirm → results) from the list/detail CRUD in `/gestiones`.

## Data Flow

```
User opens /gestiones/importar
  │
  ├── ui.upload() picks .xlsx file
  │     └── `handle_upload(e)` reads e.content.read() → bytes
  │           └── parse_excel(bytes) → list[ParsedRow]
  │                 └── ui.table() renders preview
  │
  └── User clicks "Importar"
        └── importar_gestiones_sos.execute(rows)
              │
              ├── claim_kind = claim_kind_repo.get_by_name("SOS")
              ├── group = group_claim_repo.get_all()[0]
              │
              └── for each row:
                    with uow_cls() as uow:
                        existing = uow.sos_claims.get_by_number(row.gestion)
                        if existing:
                            update Claim + SosClaim
                        else:
                            create Claim + SosClaim
                    → collect result (created / updated / error)
              │
              └── return ImportResult { created, updated, errors }
                    └── ui.notify() + ui.table() with counts
```

## File Changes

| File | Action | Description |
|------|--------|-------------|
| `src/application/services/excel_parser.py` | Create | Parse `.xlsx` bytes → `list[ParsedRow]`. Map columns per spec, skip "N° Caso". |
| `src/application/use_cases/claims/importar_gestiones_sos.py` | Create | `ImportarGestionSOS` — resolves refs, iterates rows with per-row UoW, returns `ImportResult`. |
| `src/ui/pages/sos_import.py` | Create | Page at `/gestiones/importar`: file picker, preview table, Import button, result summary. |
| `tests/test_importar_gestiones.py` | Create | Unit tests for parser + use case using existing `FakeUnitOfWork` pattern. |
| `src/infrastructure/container.py` | Modify | Wire `_importar_gestiones_sos` with `SqlAlchemyUnitOfWork`, `claim_kind_repo`, `group_claim_repo`. |
| `main.py` | Modify | Add `register_sos_import_page()` call after existing gestiones registrations. |
| `src/ui/components/shell.py` | Modify | Add `("Importar", "/gestiones/importar", "upload")` to `_nav_items()`. |

## Interfaces / Contracts

```python
# src/application/services/excel_parser.py

@dataclass
class ParsedRow:
    gestion: int
    created_at: date | None          # "Fecha" column
    claimer_name: str                 # "Asegurado"
    policy_number: str                # "Póliza"
    plate: str                        # "Patente"
    category: str                     # "Categoría"
    reason: str                       # "Motivo"
    status: str                       # "Estado"
    load_user: str                    # "Carga"
    response_user: str                # "Responde"
    itr: int                          # "ITR"

ExcelParseError = named tuple (row: int, message: str)  # for row-level parse failures


def parse_excel(content: bytes, sheet_name: str = "Sheet1") -> list[ParsedRow]:
    """Parse .xlsx bytes into structured rows. Raises ValueError on missing
    required columns, skips invalid rows with collected errors."""
    ...


# src/application/use_cases/claims/importar_gestiones_sos.py

@dataclass
class RowError:
    row_index: int
    gestion: int | None
    message: str


@dataclass
class ImportResult:
    created: list[RegistrarGestionSOSOutput]
    updated: list[RegistrarGestionSOSOutput]
    errors: list[RowError]


class ImportarGestionSOS:
    def __init__(
        self,
        uow_cls: type[UnitOfWork],
        claim_kind_repo: ClaimKindRepoPort,
        group_claim_repo: GroupClaimRepoPort,
    ): ...

    def execute(self, rows: list[ParsedRow]) -> ImportResult:
        # 1. Resolve claim_kind_id (fail if not found)
        # 2. Resolve group_id (first active group, fail if none)
        # 3. For each row: try/except around per-row UoW
        #    - if sos_claim exists → update Claim + SosClaim
        #    - else → create Claim + SosClaim (claimed_amount=0.01)
```

## Testing Strategy

| Layer | What to Test | Approach |
|-------|-------------|----------|
| Unit | Excel parser: column mapping, date parsing, missing "N° Gestión", wrong sheet name | Pure function tests — generate `.xlsx` with `openpyxl` in-memory, feed to `parse_excel()` |
| Unit | Import use case: create new, update existing, duplicate gestion in file, all-row error isolation | `FakeUnitOfWork` + `InMemoryClaimRepository` / `InMemorySosClaimRepository` (existing test pattern) |
| Unit | Kind/group resolution: found vs not-found | Fake repos returning `None`, expect early abort |

## Migration / Rollout

No migration required. Uses existing tables (Claim, SosClaim). New code is additive — separate page, separate use case, no existing code modified beyond wiring + nav.

## Open Questions

- [ ] Exact sheet name in the external SOS export — configurable default currently `"Sheet1"`, confirm with business
