# Design: UI Table Refactoring (6 Pages)

## Technical Approach

Convert 6 pages from manual `ui.row()` layouts to native `ui.table()` components. The refactoring is **non-breaking** — sorting, filtering, pagination, and dialogs remain identical. **Key change for gestiones.py**: disable row-click navigation; all actions trigger via inline action icons only.

Create reusable **Badge** and **ActionButton** helpers in `src/ui/components/table_helpers.py`. Apply consistent CSS class `table-inactive-row` for inactive rows (orange left border, opacity 0.55).

Use **data preparation layer** pattern: pre-compute all lookups (agent names, payment counts, NC flags) BEFORE table instantiation to prevent N+1 queries during render.

---

## Architecture Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| **Table Component** | NiceGUI `ui.table()` (Quasar q-table) | Native semantic HTML, built-in sorting, accessibility (ARIA labels), no custom DOM manipulation required |
| **Reusable Helpers** | New file `src/ui/components/table_helpers.py` with `Badge()` and `ActionButton()` functions | Reduce duplication across 6 pages; consistent styling; single maintenance point |
| **Data Prep Pattern** | Pre-compute all lookups (agents, payment counts, NC flags) in single pass before table render | Prevent N+1 queries; O(N) complexity; no nested loops during component instantiation |
| **Inactive Row Styling** | CSS class `.table-inactive-row` (left border 2px orange-400, opacity 0.55) | Reusable across all 6 pages; no row-level callback lambdas; managed globally in stylesheet |
| **Action Icons** | Individual visible icons per row (NOT dropdown menu); conditional rendering by entity state | Spec requirement (gestiones.py: row click disabled); clear intent; tooltip labels; matches current icon visibility logic |
| **Column Definitions** | Static `COLUMNS` list per page (dict array format for `ui.table`) | Reusable, testable, separates schema from rendering logic |
| **Sorting & Filtering State** | Preserve existing `_sort_col`, `_sort_dir`, `_page` variables; migrate to work with prepared data | Minimal behavioral change; existing filter logic remains; only table rendering changes |

---

## Data Flow

```
┌─────────────────────────────────────────┐
│ Page Load / Filter Change               │
│ (gestiones.py, pagos.py, etc.)          │
└────────────┬────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────┐
│ Fetch Raw Data from Use Cases           │
│ (ObtenerGestiones, ObtenerPagos, etc.)  │
└────────────┬────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────┐
│ _prepare_*_data() — PRE-COMPUTE LOOKUPS │
│ • Fetch all agents, vias, kinds (once)  │
│ • Count payments & NC flags per claim   │
│ • Build enriched dict[] for table rows  │
└────────────┬────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────┐
│ Apply Filters & Sort (on prepared data) │
│ (existing filter logic unchanged)       │
└────────────┬────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────┐
│ Paginate (slice for page size)          │
│ (_PAGE_SIZE = 12 items/page)            │
└────────────┬────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────┐
│ Pass Prepared Data to ui.table()        │
│ columns=COLUMNS, rows=prepared_rows     │
└────────────┬────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────┐
│ Render Table with Action Icons          │
│ • Badge() for status columns            │
│ • ActionButton() for inline icons       │
│ • .table-inactive-row CSS on rows       │
└─────────────────────────────────────────┘
```

---

## File Changes

| File | Action | Description |
|------|--------|-------------|
| `src/ui/components/table_helpers.py` | Create | New reusable `Badge()` and `ActionButton()` components with Tailwind styling |
| `src/ui/assets/style.css` (or global style) | Create/Modify | Add `.table-inactive-row` CSS class (border-left 2px orange-400, opacity 0.55) |
| `src/ui/pages/gestiones.py` | Modify | Replace manual `ui.row()` with `ui.table()`, inline action icons, disable row click |
| `src/ui/pages/pagos.py` | Modify | Replace manual `ui.row()` with `ui.table()`, reuse Badge/ActionButton helpers |
| `src/ui/pages/facturacion.py` | Modify | Replace manual `ui.row()` with `ui.table()` |
| `src/ui/pages/periodos.py` | Modify | Replace manual `ui.row()` with `ui.table()`, nested table for grupos |
| `src/ui/pages/grupos.py` | Modify | Detail view only; table structure may already be present or need minimal updates |
| `src/ui/pages/documentos.py` | Modify | Replace manual `ui.row()` with `ui.table()` for document gallery |

---

## Interfaces & Contracts

### Badge Component

```python
def Badge(text: str, color: str = 'gray', size: str = 'text-xs') -> ui.label:
    """
    Render a status badge with consistent styling.
    
    Args:
        text: Badge label text (e.g., 'Activo', 'Pendiente')
        color: Color name ('green', 'red', 'yellow', 'blue', 'purple', 'gray')
        size: Tailwind size class ('text-xs', 'text-sm', etc.)
    
    Returns:
        ui.label with badge classes
    
    Example:
        Badge('Resuelto', 'green')
    """
```

### ActionButton Component

```python
def ActionButton(
    icon: str,
    label: str = '',
    on_click=None,
    color: str = '',
    disabled: bool = False,
    tooltip_position: str = 'top'
) -> ui.button:
    """
    Render a consistent action button (edit, delete, toggle, etc.).
    
    Args:
        icon: Material Design icon name ('edit', 'delete', 'group', 'receipt_long', etc.)
        label: Tooltip text when hovering
        on_click: Click handler function
        color: Optional Tailwind color class (e.g., 'text-red-500')
        disabled: Disable button if True
        tooltip_position: Tooltip position ('top', 'right', 'bottom', 'left')
    
    Returns:
        ui.button with action styling
    
    Example:
        ActionButton('edit', 'Editar', on_click=lambda: edit_dialog(item), color='text-blue-500')
    """
```

### Data Preparation Pattern

```python
def _prepare_<page>_data(container) -> list[dict]:
    """
    Pre-compute all lookups before table render.
    
    Returns:
        List of enriched row dicts ready for ui.table(columns=..., rows=...)
    
    Structure:
        [
            {
                'id': '...', 'name': '...', 'status': '...', 'active': True/False, ...
            },
            ...
        ]
    """
```

---

## Testing Strategy

| Layer | What to Test | Approach |
|-------|------------|----------|
| **Unit** | Badge() and ActionButton() render correctly with all color/state combinations | Test component directly; verify Tailwind classes applied |
| **Integration** | Table renders with correct data; pagination, sorting, filtering work | Load each page; apply filters; click headers; navigate pages |
| **E2E** | Action icons open correct dialogs; row click does NOT navigate (gestiones.py); inactive rows styled correctly | Manual browser testing; verify dialogs appear; check CSS on inactive rows |
| **Performance** | No N+1 queries during table render; <500ms refresh time for 1000+ rows | Profile `_prepare_*_data()` call; measure component instantiation time |

---

## Migration / Rollout

No data migration required. All entity schemas and use cases remain unchanged. Refactoring is **UI-only**.

**Rollout sequence** (low to high risk):
1. **facturacion.py** (simplest; 6 columns, no complex actions)
2. **pagos.py** (14 columns, NC logic; reuses gestiones dialogs)
3. **periodos.py + grupos.py** (nested tables; stats panels)
4. **documentos.py** (multi-entity, document upload logic)
5. **gestiones.py** (highest complexity; row-click behavior change)

Each page tested individually in browser before moving to next.

---

## Open Questions

- [ ] Does NiceGUI `ui.table()` support custom row CSS classes (e.g., applying `table-inactive-row` class to specific rows)? If not, fallback to JavaScript row styling or CSS attribute selectors.
- [ ] Should action icons be rendered as a custom cell renderer in the table, or as a separate row component below the table? (Recommend testing cell renderer first.)
- [ ] Does `ui.table()` trigger `.on('update:model-value')` events for sorting/filtering, or do we need manual header click handlers? (Check NiceGUI docs.)

---

**Next**: sdd-tasks (break into implementation tasks per page)
