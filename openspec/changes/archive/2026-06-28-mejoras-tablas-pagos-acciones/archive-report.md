# Archive Report: mejoras-tablas-pagos-acciones

## Summary

| Field | Value |
|-------|-------|
| Change | mejoras-tablas-pagos-acciones |
| Completion date | 2026-06-28 |
| Tasks completed | 31 / 32 (1 intentionally skipped) |
| Verdict | PASS WITH WARNINGS |

## Features Implemented

1. **Auto-fit table columns** — 10 table views updated: gestiones, pagos, documentos, facturacion, grupos, periodos (invoices + NC), gestiones_detalle (payments + docs), gestiones_nueva (grouped claims)
2. **Inactive row highlighting** — `opacity-50` on rows where `active=False` across gestiones, pagos, facturacion, grupos, periodos
3. **Document type column** — Shows entity type (Gestión, Factura, Grupo, Pago, NC) via `get_document_entity_types()` instead of hardcoded "documento"
4. **Auto-generate payments checkbox** — "Generar pagos automáticamente" on Tres Arroyos creation form, triggers `RegistrarPagoUseCase` per claim
5. **Payment count column** — "Cant. Pagos" in gestiones table, computed via in-memory payment count in `ObtenerGestiones`
6. **Action icons** — "more_vert" dropdown per gestion row: edit, edit-group, unlink-group, add-payment, credit-note
7. **DTO changes** — `GestionDTO.payment_count: int = 0` and `group_id: UUID | None`
8. **Shared dialog extraction** — `pago_dialog` and `credito_dialog` extracted to `src/ui/dialogs/pago_dialog.py`

## Files Modified

| File | Action |
|------|--------|
| `src/domain/models/entities.py` | Modify — `group_id`, `payment_count` on `GestionDTO` |
| `src/application/use_cases/claims/obtener_gestiones.py` | Modify — populate `group_id` + `payment_count` |
| `src/domain/ports/repositories.py` | Modify — add `get_document_entity_types()` to `DocumentRepoPort` |
| `src/adapters/persistence/sqlalchemy_document_repository.py` | Modify — implement `get_document_entity_types()` |
| `src/adapters/persistence/inmemory_document_repository.py` | Modify — stub `get_document_entity_types()` |
| `src/ui/pages/gestiones.py` | Modify — auto-fit cols, inactive rows, payment_count col, action icons |
| `src/ui/pages/gestiones_nueva.py` | Modify — auto-generate payment checkbox |
| `src/ui/pages/gestiones_detalle.py` | Modify — extract dialogs to shared module |
| `src/ui/pages/documentos.py` | Modify — entity type col + auto-fit |
| `src/ui/pages/pagos.py` | Modify — auto-fit cols + inactive rows |
| `src/ui/pages/facturacion.py` | Modify — auto-fit cols + inactive rows |
| `src/ui/pages/grupos.py` | Modify — auto-fit cols + inactive rows |
| `src/ui/pages/periodos.py` | Modify — auto-fit cols + inactive rows |
| `src/ui/dialogs/__init__.py` | Create — shared dialog functions |
| `src/ui/dialogs/pago_dialog.py` | Create — extracted `pago_dialog` + `credito_dialog` |

## Specs Synced

| Domain | Action | Details |
|--------|--------|---------|
| claim-listing | Updated | Added Payment Count Column, Inline Action Icons, Visual Distinction for Inactive Rows, Auto-fit Table Columns requirements (+ 16 scenarios) |
| document-gallery | Updated | Added Entity Type Column, Document Type Repository Method requirements (+ 6 scenarios) |
| claim-registration | Updated | Added Auto-Generate Payments Checkbox requirement (+ 5 scenarios) |
| claim-detail | Updated | Added Shared Payment Dialog, Shared NC Dialog requirements |

## Known Limitations & Decisions

1. **Task 5.3 (edit_claim_dialog) skipped** — The edit icon navigates to `/gestiones/{id}` (detail page) instead of opening an inline edit dialog. User-confirmed decision.
2. **Auto-pay checkbox default** — Changed from default-checked `value=True` to `value=False` per spec (warning found in verify phase, fixed during apply).
3. **NC edit dialog added** — Replaced info notification with `editar_nc_dialog` for claims with existing NCs (warning found in verify phase, fixed during apply).
4. **`GestionDTO` location** — Defined in `obtener_gestiones.py` rather than `entities.py` as the design file suggested. Fields are correctly present.
5. **Cross-cutting UI changes** — Auto-fit and inactive row styling for pagos, facturacion, grupos, periodos pages were applied but are documented only at implementation level (no separate domain spec for each). Archived spec in this folder contains full details.

## Engram Artifact Lineage

| Artifact | Observation ID |
|----------|---------------|
| sdd/mejoras-tablas-pagos-acciones/proposal | #215 |
| sdd/mejoras-tablas-pagos-acciones/design | #216 |
| sdd/mejoras-tablas-pagos-acciones/spec | #217 |
| sdd/mejoras-tablas-pagos-acciones/tasks | #218 |
| sdd/mejoras-tablas-pagos-acciones/verify-report | #220 |
| Fix: verify warnings (checkbox default + NC dialog) | #219 |
| sdd/mejoras-tablas-pagos-acciones/archive-report | (this artifact) |

## Archive Contents

- proposal.md ✅
- spec.md ✅
- design.md ✅
- tasks.md ✅ (31/32 tasks complete)
- verify-report.md ✅
- archive-report.md ✅
