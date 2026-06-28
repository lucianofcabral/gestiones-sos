# Tasks: UI Table Refactoring

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | 1500–2000 (6 pages ~300–350 each + new helpers + CSS + tests) |
| 400-line budget risk | High |
| Chained PRs recommended | Yes |
| Suggested split | 3 work units (helpers + styles, Phase 1 pages, Phase 2 pages) |
| Delivery strategy | auto-chain (per SDD config) |
| Chain strategy | stacked-to-main |

**Decision needed before apply**: No
**Chained PRs recommended**: Yes
**Chain strategy**: stacked-to-main
**400-line budget risk**: High

### Suggested Work Units

| Unit | Goal | Est. Lines | Likely PR | Notes |
|------|------|-----------|-----------|-------|
| 1 | Create helpers, CSS, test page | 200–250 | PR 1 | Foundation; no page changes; mergeable standalone |
| 2 | Migrate gestiones.py + pagos.py | 600–700 | PR 2 | Depends on PR 1; ~2 days; merges to main |
| 3 | Migrate facturacion, periodos, grupos, documentos | 700–800 | PR 3 | Depends on PR 2; ~1 day; merges to main |
| 4 | Final testing, docs, cleanup | 100–150 | PR 4 (optional) | Post-implementation tests; polish; changelog |

---

## Phase 1: Foundation & Helpers (Day 1)

- [ ] 1.1 Create `src/ui/components/table_helpers.py` with Badge(text, color, size) and ActionButton(icon, label, on_click, color, disabled, tooltip_position) components; implement BadgeColor enum (GREEN, RED, YELLOW, BLUE, GRAY, ORANGE, PURPLE)
- [ ] 1.2 Add `.table-inactive-row` CSS class to `src/ui/assets/style.css` (left border 2px orange-400, opacity 0.55); ensure dark theme consistency
- [ ] 1.3 Create test page `/test-ui-helpers` displaying all badge colors, action buttons, and inactive row styling; verify no console errors
- [ ] 1.4 Remove test page after verification and commit Phase 1 helpers-only PR

---

## Phase 2: Gestiones.py & Pagos.py (Days 2–3)

### Gestiones.py

- [ ] 2.1 Create `_prepare_gestiones_data(container)` function: pre-fetch claims, kinds, groups, payments, NCs in one pass; return list of dicts with tipo, gestion, asegurado, poliza, patente, monto, fecha, resuelto, cant_pagos, active, has_group, has_nc, solved fields
- [ ] 2.2 Define `GESTIONES_COLUMNS` list with 10 columns (tipo, gestion, asegurado, poliza, patente, monto, fecha, resuelto, cant_pagos, acciones); set sortable=True, alignments, min-widths
- [ ] 2.3 Replace manual header rendering (ui.row loop) with `ui.table(columns=GESTIONES_COLUMNS, rows=prepared_data, row_key='id')`; remove old sort arrow code; apply inactive row CSS class
- [ ] 2.4 Create `_render_gestiones_actions(claim_id, row_data)` function returning ui.row with 5 icons (edit, grupo, pagos, NC, delete) using ActionButton helper; wire each to existing dialog handlers
- [ ] 2.5 Integrate actions into table (test cell renderer or fallback to separate row); ensure no layout shifts
- [ ] 2.6 Migrate `_apply_filters()` to work with prepared data; ensure all 6 filter combinations work; reset pagination on filter change
- [ ] 2.7 Preserve custom pagination logic (12 items/page, prev/next buttons); update handlers to call `table.update(rows=slice)`
- [ ] 2.8 Comprehensive manual test: all columns sort, all filters work, pagination works, icons functional, no row-click, inactive rows highlighted, no console errors

### Pagos.py

- [ ] 2.9 Create `_prepare_pagos_data(container)` function enriching payments with agents, payment_vias, claims, groups, kinds, NCs lookups (14 fields); avoid N+1 queries
- [ ] 2.10 Define `PAGOS_COLUMNS` (14 columns); replace manual header + row rendering with `ui.table()`; apply inactive row CSS
- [ ] 2.11 Create action icons for pagos (edit, toggle, view NC) using ActionButton helper; wire to existing handlers
- [ ] 2.12 Comprehensive manual test: all 14 columns visible, sorting works, NC status badges correct, pagination works, actions functional

---

## Phase 3: Facturacion.py, Periodos.py, Grupos.py, Documentos.py (Days 4–5)

### Facturacion.py

- [ ] 3.1 Create `_prepare_facturacion_data(container)` function (6 columns)
- [ ] 3.2 Replace manual rendering with `ui.table()`; apply inactive row CSS; define action icons
- [ ] 3.3 Comprehensive manual test: all 6 columns, sorting, filtering, pagination, actions work

### Periodos.py

- [ ] 3.4 Create `_prepare_periodos_data(container)` function for main periodo rows and nested invoice/NC tables
- [ ] 3.5 Migrate main periodo table to `ui.table()` inside expandable card
- [ ] 3.6 Migrate nested invoice table (within period card) to `ui.table()`; ensure card layout intact
- [ ] 3.7 Migrate nested NC table to `ui.table()`; same layout constraints
- [ ] 3.8 Comprehensive manual test: main table + nested tables render, all interactions work, card expansion works

### Grupos.py

- [ ] 3.9 Create `_prepare_grupos_data(container)` function (6 columns with stats aggregation)
- [ ] 3.10 Replace manual rendering with `ui.table()`; apply inactive row CSS; define edit/delete action icons
- [ ] 3.11 Comprehensive manual test: all columns, stats correct, sorting works, actions functional

### Documentos.py

- [ ] 3.12 Create `_prepare_related_entities(entities, container)` function pre-computing all entity lookups (claims, invoices, groups)
- [ ] 3.13 Migrate related-entities table to `ui.table()` with category color badges; preserve row-click to open entity dialog
- [ ] 3.14 Decide: convert list-view/category-view tables to `ui.table()`, or keep manual rows? If converting, apply same pattern; if keeping, no changes
- [ ] 3.15 Comprehensive manual test: related-entities table displays all entities, badges color-coded, dialogs open on click; list-view and category-view work as before

---

## Phase 4: Integration & Cross-Page Testing (Day 6)

- [ ] 4.1 Run full test suite: `pytest tests/` to ensure no regressions; all tests pass
- [ ] 4.2 Comprehensive browser regression test: all 6 pages end-to-end, all sorting/filtering/pagination/actions work, dark theme consistent, no visual regressions
- [ ] 4.3 Verify N+1 query fix: profile DB logs for all 6 pages; confirm no N+1 queries during table render
- [ ] 4.4 Performance check: table refresh time &lt;500ms for 1000+ rows (if applicable)

---

## Phase 5: Cleanup & Documentation (Day 7+)

- [ ] 5.1 Update component documentation (if `docs/` exists) with Badge/ActionButton usage examples
- [ ] 5.2 Update any architecture docs or README referencing old manual row patterns
- [ ] 5.3 Commit message: "refactor(ui): migrate 6 pages from manual ui.row() to ui.table(); add Badge + ActionButton helpers; ~1500 LOC"

---

## Key Implementation Notes

### Per-Phase Dependencies
- Phase 1 (helpers) is standalone; all other phases depend on it
- Phase 2 (gestiones, pagos) are independent but recommended together (similar patterns)
- Phase 3 pages are independent of each other; can be parallelized if needed
- Phase 4 (integration tests) depends on all Phase 2–3 pages being complete

### Critical Design Constraints
- **Gestiones.py NO row-click**: All navigation ONLY via edit icon (icon click → _open_edit_dialog)
- **Inactive rows**: CSS class `.table-inactive-row` applied to &lt;tr&gt; or parent div; no JavaScript state
- **Pre-computed data**: All N+1 lookups resolved BEFORE table render; _prepare_*_data() functions run once per page load
- **Column Definitions**: Static COLUMNS lists (Python dicts) for reusability and testability
- **Pagination**: Custom 12-item-per-page pagination with manual prev/next buttons; NOT Quasar pagination

### Testing Checklist Per Page
- ✅ All columns visible and correct width
- ✅ Sorting works on all columns (click header → sort arrow changes)
- ✅ All filters work independently + in combination
- ✅ Pagination: 12 items/page, prev/next buttons functional
- ✅ Action icons render conditionally (grupo only if group_id set, etc.)
- ✅ Action icon clicks open correct dialogs
- ✅ Inactive rows highlighted (orange left border, opacity 0.55)
- ✅ No console errors or warnings
- ✅ Responsive design intact

### Risk Mitigation
- **Cell renderers (Task 1.5 risk)**: If ui.table() doesn't support cell renderers for action icons, fallback to separate row component below table (low impact; existing codebase pattern)
- **Nested tables (Task 3.6–3.7)**: Test periodos card expansion with nested ui.table() instances; ensure no layout conflicts
- **Dark theme (Task 1.2)**: Verify all badge colors render correctly in dark mode; test inactive row orange visibility in dark background

---

## Files Modified/Created

| File | Action | Complexity |
|------|--------|-----------|
| `src/ui/components/table_helpers.py` | Create | Low (simple functions) |
| `src/ui/assets/style.css` | Create/Modify | Low (1–2 CSS rules) |
| `src/ui/pages/gestiones.py` | Modify | High (row-click removal + icons + no N+1) |
| `src/ui/pages/pagos.py` | Modify | Medium (table migration, 14 columns) |
| `src/ui/pages/facturacion.py` | Modify | Low (table migration, 6 columns) |
| `src/ui/pages/periodos.py` | Modify | High (nested tables within card) |
| `src/ui/pages/grupos.py` | Modify | Medium (table + stats aggregation) |
| `src/ui/pages/documentos.py` | Modify | Medium (multiple tables, entity resolution) |

---

## Handoff Notes for Apply Phase

1. **Enqueue work units in order** (1 → 2 → 3) to respect dependencies
2. **Each work unit is a discrete PR** with its own verification and commit message
3. **Before merging each PR**, run targeted manual test (per Testing Checklist)
4. **Monitor DB logs** during Phase 4 to confirm N+1 elimination
5. **If cell renderers don't work** (Task 1.5), decide on fallback row component pattern; update periodos.py accordingly
6. **Final PR (Phase 5)** is optional if all code is clean; useful for changelog + docs updates only
