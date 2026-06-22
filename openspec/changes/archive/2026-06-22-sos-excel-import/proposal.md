# Proposal: SOS Excel Import

## Intent

Users manually re-enter SOS claims one-by-one via the UI form, which is slow and error-prone. The external SOS system exports a structured Excel; this change ingests it directly — upserting claims in bulk while preserving existing data.

## Scope

### In Scope
- New use case `ImportarGestionesSOS` — parse Excel rows and upsert (create or update) each claim per-row
- Excel parsing module — read `.xlsx`, map columns to domain fields, skip "N° Caso"
- Runtime `claim_kind_id` lookup via `ClaimKindRepoPort.get_by_name("SOS")` with fallback to a sensible default
- Per-row UoW — each row is its own transaction; failures on one row do not block others
- New UI page `/gestiones/importar` — file upload + result summary
- Default `claimed_amount = 0.01`

### Out of Scope
- Batch all-or-nothing transaction model (deferred)
- Drag-and-drop upload (uses standard file picker)
- Scheduled/automated imports (manual trigger only)
- Excel template generation or download
- Validation of Excel column presence before parsing

## Capabilities

### New Capabilities
- `sos-import`: Upload Excel file with SOS claims, parse, upsert, and report results per-row

### Modified Capabilities
- None

## Approach

1. **Use case** — `ImportarGestionSOS(cls, uow, claim_kind_repo, group_claim_repo)`. Each row: check if `gestion` exists (`get_by_number`), if yes → update (Claim + SosClaim), if no → create. Wraps each row in its own UoW transaction.
2. **Excel parser** — `src/application/use_cases/claims/excel_parser.py`. Read filename + sheet from config. Map columns using fixed header names. Return list of row dicts.
3. **Result model** — `ImportResult` with lists of: `created`, `updated`, `skipped`, `errors`.
4. **UI page** — `/gestiones/importar` with `ui.upload()` for file selection, table for result summary.
5. **Wiring** — Register in `Container` as `importar_gestiones_sos`.

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `src/application/use_cases/claims/` | New | `importar_gestiones_sos.py`, `excel_parser.py` |
| `src/infrastructure/container.py` | Modified | Wiring for new use case |
| `src/ui/pages/` | New | `gestiones_importar.py` |
| `src/ui/routes/` | Modified | Register new page route |
| `tests/` | New | Unit + integration tests |
| `pyproject.toml` | Modified | Add `openpyxl` dependency |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| UNIQUE constraint on `gestion` at DB level | Medium | Upsert via `get_by_number` within UoW before insert |
| Missing `claim_kind` "SOS" or missing default | Low | Fail early with clear error; seed migration in docs |
| Empty/malformed Excel columns | Medium | Row-level try/except; skip row, add to errors list |
| Excel file renamed or sheet missing | Low | Configurable filename/sheet; clear error if not found |

## Rollback Plan

Remove the `importar_gestiones_sos` use case wiring and the UI page. Remove `openpyxl` from dependencies. DB schema is unchanged (uses existing tables only).

## Dependencies

- `openpyxl` (or `xlrd`/`pandas`) for Excel parsing

## Success Criteria

- [ ] User uploads the Excel file and sees a result table with rows created/updated/skipped/errors
- [ ] Re-uploading the same file updates existing rows (gestion match) instead of duplicating
- [ ] A row with missing `Fecha` or `N° Gestión` is skipped without crashing the whole import
- [ ] All new code has unit test coverage > 80%
