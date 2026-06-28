# Proposal: Document Category View

## Intent

Users need to see documents organized by the entity they're linked to (Claim, Invoice, Group) instead of a flat list. Selecting a document should show all its linked entities with category-specific details, and navigating to the entity's edit dialog should be one click away.

## Scope

### In Scope
- Toggle between List View (existing flat table) and Category View (expandable sections per entity type)
- Category View with 3 sections: Gestiones, Facturas, Grupos — same document may appear in multiple
- Document row selection drives a master-detail "related entities" table at page top
- Related-entities table shows entity-specific info per row (invoice number+period, group name+count, claim tipo+nro+patente+poliza+cliente)
- Clicking related-entity row opens existing dialog/page for that entity
- `get_document_entities()` added to `DocumentRepoPort` protocol

### Out of Scope
- New entity dialogs — reuse existing from facturacion.py, grupos.py, gestiones_detalle.py
- Document upload — unchanged
- Entity info columns are display-only (no inline editing)

## Capabilities

### New Capabilities
- None — this is a UI enhancement to the existing page

### Modified Capabilities
- `document-gallery`: page gains view toggle, category grouping, document selection, and entity navigation

## Approach

- Single-page change in `src/ui/pages/documentos.py`: wrap existing content + new views inside a reactive component tree
- **Toggle**: `ui.toggle(["Lista", "Categorías"])` controls which `@ui.refreshable` is rendered
- **Category View**: query `document_repo.get_all()`, for each doc call `get_document_entities()`, group entities by `entity_type`, render `ui.expansion` per category
- **Related-entities table**: persists above both views; selected doc ID stored as reactive state; on change, fetch entities + enrich with entity detail (Invoice/GroupClaim/GestionDetalleDTO)
- **Entity navigation**: table rows carry entity_type + entity_id; click dispatches to `_invoice_dialog(id)`, `_edit_group(group)`, or `ui.navigate.to(f"/gestiones/{id}")`
- Enrichment queries happen client-side via container (no new use cases needed)

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `src/ui/pages/documentos.py` | Modified | Toggle, category view, entity selection + detail table |
| `src/domain/ports/repositories.py` | Modified | Add `get_document_entities` to `DocumentRepoPort` |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| N+1 queries for entity enrichment | Med | Lazy load details only for selected doc; accept in MVP |
| Category performance with many docs | Low | In-memory grouping; pagination deferred |

## Rollback Plan

Revert changes to `documentos.py` and `repositories.py`. Toggle defaults to List View — no user-facing breakage if entity nav fails.

## Dependencies

None — all entity repos and dialogs already exist.

## Success Criteria

- [ ] Toggle switches between List and Category views without page reload
- [ ] Category View shows 3 expandable sections with correct doc counts
- [ ] Selecting a doc row (in either view) populates the related-entities table
- [ ] Each entity row shows correct category-specific info
- [ ] Clicking an entity row opens the correct dialog/page
- [ ] Existing List View and download still work unchanged
