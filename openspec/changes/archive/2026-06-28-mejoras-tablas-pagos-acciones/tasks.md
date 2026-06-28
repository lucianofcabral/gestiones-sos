# Tasks: Mejoras Tablas Pagos Acciones

| Field | Value |
|-------|-------|
| Estimated changed lines | ~580–680 |
| 800-line budget risk | Medium |
| Chained PRs recommended | No |
| Delivery strategy | ask-on-risk |

Decision needed before apply: Yes
Chained PRs recommended: No
Chain strategy: pending
400-line budget risk: Medium

## Phase 1: Foundation — DTO & Repo

- [x] 1.1 `entities.py`: add `group_id` and `payment_count` to `GestionDTO`
- [x] 1.2 `obtener_gestiones.py`: populate new fields — iterate all payments counting per claim_id
- [x] 1.3 `repositories.py`: add `get_document_entity_types()` to `DocumentRepoPort`
- [x] 1.4 `sqlalchemy_document_repository.py`: implement — query `document_entities`, return type list
- [x] 1.5 `inmemory_document_repository.py`: add stub returning `[]`

## Phase 2: Auto-fit Columns + Inactive Rows

- [x] 2.1 `gestiones.py`: content cols → `flex-1`+`truncate`, fixed widths for Tipo/Monto/Fecha/Resuelto
- [x] 2.2 `gestiones_nueva.py` grouped table: `Asegurado` → `flex-1`
- [x] 2.3 `gestiones_detalle.py`: payments (`Pagador`,`Beneficiario`) and docs (`Nombre`) → `flex-1`
- [x] 2.4 `pagos.py`: `Cliente`,`Dominio`,`Póliza` → `flex-1`
- [x] 2.5 `facturacion.py`: `Descripción` → `flex-1`
- [x] 2.6 `grupos.py`: `Nombre`,`Descripción` → `flex-1`
- [x] 2.7 `periodos.py`: invoice `Descripción` → `flex-1`; NC table unchanged
- [x] 2.8 `documentos.py`: `Nombre` → `flex-1`
- [x] 2.9 `gestiones.py`: `opacity-50` on rows where `active==False`
- [x] 2.10 `pagos.py`,`facturacion.py`,`grupos.py`,`periodos.py`: `opacity-50` when entity `active==False`

## Phase 3: Document Type Column

- [x] 3.1 `documentos.py`: replace `doc.type` with entity type label from `get_document_entity_types()`, mapped via `_CATEGORY_LABELS`
- [x] 3.2 Add `payment`/`credit_note` entries to `_CATEGORY_LABELS` and `_CATEGORY_COLORS`
- [x] 3.3 No entities → `"—"`; multiple → show first + tooltip with all

## Phase 4: Payment Auto-generation

- [x] 4.1 `gestiones_nueva.py`: add checkbox "Generar pagos automáticamente" below document upload
- [x] 4.2 In `_on_submit_all`, if checked: loop claims, call `RegistrarPagoUseCase` (SM→Prestador→Transferencia, amount=claimed_amount)
- [x] 4.3 Warn if SM/Prestador/Transferencia missing; report partial generation as "Pagos generados: X de Y"

## Phase 5: Shared Dialogs

- [x] 5.1 Create `src/ui/dialogs/__init__.py`
- [x] 5.2 Create `src/ui/dialogs/pago_dialog.py`: extract `_pago_dialog` + add `credito_dialog` (locked payer=SOS, payee=SM, via=NC)
- [ ] 5.3 Create `src/ui/dialogs/edit_claim_dialog.py`: reusable dialog for editing claim fields
- [x] 5.4 `gestiones_detalle.py`: replace inline `_pago_dialog` with import; remove extracted code

## Phase 6: Action Icons

- [x] 6.1 `gestiones.py`: add action column (`w-40`, label `""`) to `_gest_columns`
- [x] 6.2 Render icons: edit (navigate), edit-group (call `edit_group_dialog`), unlink (call `ActualizarGrupoDeGestion` with `None`), add-payment (open `pago_dialog`), credit-note (open `credito_dialog`)
- [x] 6.3 Show group actions only when `group_id` set; NC dialog variant based on existing NC check
- [x] 6.4 Wire `on_save` → `_render_gestiones.refresh()`

## Phase 7: Payment Count Column

- [x] 7.1 `gestiones.py`: add `("Cant. Pagos","w-16",lambda g: g.payment_count)` after "Resuelto" in `_gest_columns`
- [x] 7.2 Render `ui.label(str(g.payment_count)).classes("text-sm w-16")` in each row
- [x] 7.3 Sort by `payment_count` works via existing lambda key
