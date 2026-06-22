# Tasks: SOS Excel Import

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | ~710 |
| 800-line budget risk | Low |
| Chained PRs recommended | No |
| Suggested split | Single PR |
| Delivery strategy | single-pr (auto-forecast) |

Decision needed before apply: No
Chained PRs recommended: No
Chain strategy: single-pr
800-line budget risk: Low

### Suggested Work Units

| Unit | Goal | Likely PR | Notes |
|------|------|-----------|-------|
| 1 | Excel parser + use case + UI + wiring | Single PR | All additive, no existing code changed beyond wiring. ~710 lines within budget. |

## Phase 1: Foundation — Excel Parser

- [x] 1.1 Create `src/application/services/excel_parser.py` — `ParsedRow` dataclass, `parse_excel(content: bytes, sheet_name: str) -> list[ParsedRow]`, `ExcelParseError` tuple. Map columns per spec, skip "N° Caso", handle date parsing, wrap each row parse in try/except.
- [x] 1.2 Add unit tests for `parse_excel` — valid rows, missing `N° Gestión` column, wrong sheet name, missing `Fecha`, non-integer `gestion`, empty file, all columns present with correct mapping.

## Phase 2: Core Implementation — Use Case

- [x] 2.1 Create `src/application/use_cases/claims/importar_gestiones_sos.py` — `ImportResult` dataclass (created/updated/errors), `RowError` dataclass, `ImportarGestionSOS` class accepting `uow_cls: type[UnitOfWork]`, `claim_kind_repo`, `group_claim_repo`. Pre-resolve `claim_kind_id` and `group_id`, per-row UoW with create vs update logic (`RegistrarGestionSOSOutput` on success, row-level try/except on failure).

## Phase 3: Integration — Wiring & UI

- [x] 3.1 Wire `importar_gestiones_sos` in `src/infrastructure/container.py` — import use case, instantiate with `SqlAlchemyUnitOfWork`, `claim_kind_repo`, `group_claim_repo`.
- [x] 3.2 Create `src/ui/pages/sos_import.py` — `/gestiones/importar` page with `ui.upload()` (`.xlsx` only, 10 MB limit), preview table of parsed rows, "Importar" button, result summary table (created/updated/errors). Use `AppShell`.
- [x] 3.3 Register route — add `register_sos_import_page()` call in `main.py`.
- [x] 3.4 Add nav link — append `("Importar", "/gestiones/importar", "upload")` to `_nav_items()` in `src/ui/components/shell.py`.

## Phase 4: Testing — Integration

- [x] 4.1 Create `tests/test_importar_gestiones.py` — end-to-end test with `InMemoryClaimKindRepository`, `InMemoryGroupClaimRepository`, `FakeUnitOfWork` (wrapping `InMemoryClaimRepository` + `InMemorySosClaimRepository`). Test: happy path (create), update existing, duplicate gestion in file, missing claim_kind aborts, no groups aborts, partial row failure isolation, result summary counts.
