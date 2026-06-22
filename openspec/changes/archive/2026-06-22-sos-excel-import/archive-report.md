# Archive Report: SOS Excel Import

**Archived**: 2026-06-22
**Change**: `sos-excel-import`
**Mode**: hybrid (filesystem + Engram)

## Summary

Implemented a bulk import pipeline for SOS claims from Excel (`.xlsx`) files exported by the external SOS system. Users can now navigate to `/gestiones/importar`, upload a file, preview parsed rows, and execute the import — which upserts each row as a Claim + SosClaim in its own transaction.

## What Was Implemented

| Feature | Description |
|---------|-------------|
| Excel Parser | `src/application/services/excel_parser.py` — pure function `parse_excel()`, `ParsedRow` dataclass, 11-column mapping per spec, skip "N° Caso" column, date parsing |
| Import Use Case | `src/application/use_cases/claims/importar_gestiones_sos.py` — `ImportarGestionSOS` class with per-row UoW, pre-resolved claim_kind + group, create vs update logic |
| UI Page | `src/ui/pages/sos_import.py` — `/gestiones/importar` with file upload (`.xlsx` only, 10 MB limit), preview table, Import button, result summary |
| Wiring | `src/infrastructure/container.py` — `importar_gestiones_sos` property wired with `SqlAlchemyUnitOfWork`, `claim_kind_repo`, `group_claim_repo` |
| Route Registration | `main.py` — `register_sos_import_page()` call added |
| Nav Link | `src/ui/components/shell.py` — `("Importar", "/gestiones/importar", "upload")` in `_nav_items()` |
| Tests | `tests/test_importar_gestiones.py` — 23 tests spanning parser, use case, and full integration pipeline |

## Files Created / Modified

| File | Action |
|------|--------|
| `src/application/services/excel_parser.py` | Created |
| `src/application/use_cases/claims/importar_gestiones_sos.py` | Created |
| `src/ui/pages/sos_import.py` | Created |
| `src/infrastructure/container.py` | Modified |
| `main.py` | Modified |
| `src/ui/components/shell.py` | Modified |
| `tests/test_importar_gestiones.py` | Created |

## Specs Synced

| Domain | Action | Details |
|--------|--------|---------|
| `sos-excel-import` | Created | New main spec at `openspec/specs/sos-excel-import/spec.md` — 7 requirements across upload, parsing, upsert, kind resolution, group resolution, error isolation, and results summary. No delta merge needed (clean add). |

## Artifact Audit

| Artifact | Path | Status |
|----------|------|--------|
| Proposal | `openspec/changes/archive/2026-06-22-sos-excel-import/proposal.md` | ✅ |
| Spec | `openspec/changes/archive/2026-06-22-sos-excel-import/spec.md` | ✅ |
| Design | `openspec/changes/archive/2026-06-22-sos-excel-import/design.md` | ✅ |
| Tasks | `openspec/changes/archive/2026-06-22-sos-excel-import/tasks.md` | ✅ |
| Verify Report | `openspec/changes/archive/2026-06-22-sos-excel-import/verify-report.md` | ✅ |
| Archive Report | `openspec/changes/archive/2026-06-22-sos-excel-import/archive-report.md` | ✅ |

## Verification Result

**PASS WITH WARNINGS** — 8/8 tasks complete, 344 tests pass (23 new + 321 pre-existing), 0 failures, 0 critical issues.

## Known Issues (from Verify Report)

1. **Dead test method** (`test_new_claim_defaults_amount` inside `TestImportarGestionSOS`) — intentionally broken, replaced by a module-level test. Runs harmlessly but has no useful assertions. Recommend removing.
2. **Parser errors silently discarded** — non-integer gestion rows are caught and skipped with `except ExcelParseError: continue`. The UI never sees them. If the business needs visibility, the parser should return collected errors alongside rows.
3. **Synchronous import in async handler** — `do_import()` is `async` but calls `use_case.execute()` synchronously, potentially blocking the NiceGUI event loop. Consider `asyncio.to_thread()` for large files.
4. **`ImportResult` uses scalar counts vs list of outputs** — design specified `list[RegistrarGestionSOSOutput]` but implementation uses `int` counters. Safe simplification (UI only needs counts), but design doc should be updated to match.

## Suggestions for Future Work

1. **Batch all-or-nothing transaction model** — currently each row is its own transaction. For strict consistency requirements, consider a single-transaction mode (noted as deferred in the original proposal).
2. **Scheduled/automated imports** — currently manual trigger only. Could add a CLI command or cron job for periodic imports.
3. **Excel template generation** — provide a downloadable template so users know the expected column format.
4. **Drag-and-drop upload** — NiceGUI supports this natively; UX improvement.
5. **Progress indication** — for large files (>1000 rows), show per-row progress during import.

## SDD Cycle Complete

The change has been fully planned, implemented, verified, and archived. Ready for the next change.
