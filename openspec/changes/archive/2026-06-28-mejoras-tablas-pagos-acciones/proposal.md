# Proposal: Mejoras Tablas Pagos Acciones

## Intent

Improve table usability across the app: auto-fit columns, highlight inactive rows, show real document types, add payment count and action icons to gestiones, and auto-generate payments for Tres Arroyos claims.

## Scope

### In Scope
1. **Auto-fit columns** in ~12 tables (replace fixed `w-*` classes)
2. **Inactive row highlighting** — visual distinction for `active=False` rows
3. **Documentos table** — show `entity_type` (claim, invoice, group_claim) instead of hardcoded "documento"
4. **Tres Arroyos creation** — checkbox to auto-generate payments
5. **Gestiones list** — add "Cantidad de Pagos" column
6. **Gestiones list** — action icons per row (edit claim, edit group, unlink group, add payment, credit note)

### Out of Scope
- Full table virtualization or pagination
- Bulk actions (select multiple rows)
- Drag-and-drop or reorderable columns
- Column visibility customization
- Backend performance optimization beyond N+1 fixes

## Capabilities

### New Capabilities
None — all changes are UI/UX enhancements to existing capabilities.

### Modified Capabilities
- `claim-listing`: Add payment_count column, action icons (edit, group/unlink, add payment, credit note), inactive row highlighting
- `document-gallery`: Show entity_type (DocumentTypeEnum) instead of hardcoded "documento"
- `claim-registration`: Add "auto-generate payments" checkbox for Tres Arroyos creation
- `claim-detail`: Expose add-payment and credit-note actions from the detail page

## Approach

1. **Auto-fit**: Selective `flex-1` + truncate, NOT a full migration. Target the worst fixed-width tables first. Add `flex-1` to content columns, keep action/via columns compact. Apply per-table, test each one.
2. **Inactive rows**: CSS class on rows where `active=False` — reduced opacity + muted text. No backend change.
3. **Document entity_type**: Read `document_entities.entity_type`, display first entity type with a tooltip if multiple entities exist.
4. **Payment auto-generation**: New flag in Tres Arroyos creation form → triggers `RegistrarPago` use case post-claim-creation. Requires backend orchestration in a new or extended use case.
5. **Payment count**: Add `payment_count: int` to `GestionDTO`. Fetch via a single COUNT subquery in `ObtenerGestiones`.
6. **Action icons**: Group icons in a compact action cell. Use a small dropdown or popover to avoid 5+ icons cluttering the row. Add-payment and credit-note open existing modals from `gestiones_detalle.py`.

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `src/ui/pages/gestiones.py` | Modified | Action icons, payment_count col, inactive styling |
| `src/ui/pages/gestiones_nueva.py` | Modified | Auto-generate payment checkbox for Tres Arroyos |
| `src/ui/pages/documentos.py` | Modified | Show entity_type, inactive styling |
| `src/domain/models/entities.py` | Modified | Add `payment_count` to GestionDTO |
| `src/application/use_cases/claims/obtener_gestiones.py` | Modified | Fetch payment count via subquery |
| `src/ui/pages/gestiones_detalle.py` | Modified | Extract payment/NC modals for reuse |
| All other table pages | Modified | Auto-fit and inactive styling pass |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Document multi-entity ambiguity | High | Show first entity type, tooltip for others |
| Table clutter with 5+ icons | Medium | Use dropdown menu or compact icon bar |
| Auto-fit breaking existing layouts | Medium | Apply per-table, test each one |
| Payment count N+1 on large datasets | Medium | Single COUNT subquery per page load |

## Rollback Plan

Each feature is independently revertible. Auto-fit: restore fixed `w-*` classes on affected tables. Action icons: hide the action column. Payment count: revert DTO + use case changes. Entity type: revert to "documento" literal. Auto-generation: remove checkbox and backend call.

## Dependencies

None external. Depends on existing `payment-crud`, `nc-payment-crud`, and `group-claim` use cases being stable.

## Success Criteria

- [ ] All 6 features functional and verified per table
- [ ] No regressions in existing table layouts or click-to-navigate behavior
- [ ] Action icons do not overflow or break row spacing on 1280px viewport
- [ ] Document type shown correctly for single-entity documents
- [ ] Payment auto-generation creates correct payment records for Tres Arroyos
