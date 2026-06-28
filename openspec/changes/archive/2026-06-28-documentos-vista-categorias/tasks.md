# Tasks: Document Category View

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | ~220–300 |
| 400-line budget risk | Low |
| Chained PRs recommended | No |
| Suggested split | Single PR |
| Delivery strategy | auto-forecast |
| Chain strategy | size-exception |

### Suggested Work Units

| Unit | Goal | Likely PR | Notes |
|------|------|-----------|-------|
| 1 | Full Document Category View — protocol → refactor → toggle → category view → entity table → navigation | PR 1 | Single PR, ~220–300 lines total |

---

## Group 1 — Foundation (protocol + refactor + helpers)

### Task 1.1 — Add `get_document_entities` to `DocumentRepoPort` protocol

**What:** Declare `get_document_entities(document_id: UUID) -> list[dict[str, Any]]` in `DocumentRepoPort`.

**Why:** Both adapters (`SqlAlchemyDocumentRepository`, `InMemoryDocumentRepository`) already implement this method, but the protocol doesn't declare it — so the container return type `DocumentRepoPort` doesn't expose it. Adding it to the protocol makes it callable from the UI layer.

**Files:**
- `src/domain/ports/repositories.py` (line ~138, after `remove_document_entity`)

**Changes:**
```python
# Add inside DocumentRepoPort class body, after remove_document_entity
def get_document_entities(self, document_id: UUID) -> list[dict[str, Any]]: ...
```

**Dependencies:** None

**Completion criteria:**
- [ ] Protocol declares `get_document_entities` with correct signature
- [ ] `mypy` passes on the protocol file
- [ ] No runtime error when calling `container.document_repo.get_document_entities(id)`

---

### Task 1.2 — Extract `_edit_group` to module-level function in `grupos.py`

**What:** Extract `_edit_group` from inside `grupos_page()` to a module-level `_edit_group_dialog(group: GroupClaim, container: Container, refresh_fn: Callable)`, so `documentos.py` can import and call it.

**Why:** When the user clicks a "Grupo" row in the related-entities table on the documentos page, we need to open the group edit dialog. Currently `_edit_group` is a closure inside `grupos_page()` — can't be imported.

**Changes in `src/ui/pages/grupos.py`:**

1. Extract lines 40-282 (full `_edit_group` body) to module-level function:
   - Signature: `def _edit_group_dialog(group: GroupClaim, container: Container, refresh_fn: Callable[[], Any]) -> None:`
   - Replace `_render_grupos.refresh()` calls with `refresh_fn()`
   - Remove `nonlocal _render_grupos` reference
   - Keep all inner closures (`_claims_in_group`, `_claims_available`, `_rebuild_members`, `_rebuild_available`, `_remove_claim_dialog`, `_add`, `_render_docs`) as-is
   - `dlg.open()` stays inside the function (last line)

2. Replace original `_edit_group` inside `grupos_page` with thin wrapper:
   ```python
   def _edit_group(group: GroupClaim) -> None:
       _edit_group_dialog(group, container, refresh_fn=_render_grupos.refresh)
   ```

3. Add `from typing import Any, Callable` to module imports (if not present).

**Caution:** The sub-dialog `_remove_claim_dialog` lives entirely inside `_edit_group`'s closure — it must move with the extracted function. The `Container` type is already imported.

**Files:**
- `src/ui/pages/grupos.py`

**Dependencies:** None (pure refactor)

**Completion criteria:**
- [ ] `_edit_group_dialog(group, container, refresh_fn)` is a module-level function
- [ ] `grupos.py` page still works: edit dialog opens, save/cancel, group list refreshes
- [ ] Function is importable from `documentos.py` without circular imports

---

### Task 1.3 — Add entity enrichment helpers in `documentos.py`

**What:** Write module-level helper functions that resolve entity details from raw `get_document_entities()` links into display-ready dicts for the related-entities table.

**Where:** New module-level functions in `src/ui/pages/documentos.py`.

**Functions to create:**

```python
from uuid import UUID
from typing import Any


def _enrich_entity(entity_link: dict[str, Any], container: Container) -> dict[str, Any] | None:
    """Resolve a single entity link into a display-ready row by type."""
    etype = entity_link["entity_type"]
    eid = entity_link["entity_id"]
    created_at = entity_link.get("created_at")
    if etype == "invoice":
        return _enrich_invoice(eid, created_at, container)
    elif etype == "claim":
        return _enrich_claim(eid, created_at, container)
    elif etype == "group_claim":
        return _enrich_group(eid, created_at, container)
    return None


def _enrich_invoice(entity_id: UUID, created_at, container) -> dict[str, Any] | None:
    invoice = container.billing_repo.get_by_id(entity_id)
    if invoice is None:
        return None
    period = container.period_repo.get_by_id(invoice.period_id) if invoice.period_id else None
    return {
        "entity_id": str(entity_id),
        "entity_type": "invoice",
        "category": "Factura",
        "created_at": created_at,
        "info_fields": {
            "Comprobante": invoice.invoice_number,
            "Período": period.period_name if period else "—",
        },
    }


def _enrich_claim(entity_id: UUID, created_at, container) -> dict[str, Any] | None:
    claim = container.claim_repo.get_by_id(entity_id)
    if claim is None:
        return None
    sos_claims = container.sos_claim_repo.get_claims_by_claim_id(claim.claim_id)
    sos = sos_claims[0] if sos_claims else None
    kind = container.claim_kind_repo.get_by_id(claim.claim_kind_id) if claim.claim_kind_id else None
    return {
        "entity_id": str(entity_id),
        "entity_type": "claim",
        "category": "Gestión",
        "created_at": created_at,
        "info_fields": {
            "Tipo": kind.name if kind else "—",
            "N°": str(sos.gestion) if sos else "—",
            "Patente": claim.plate or "—",
            "Póliza": claim.policy_number or "—",
            "Cliente": claim.claimer_name or "—",
        },
    }


def _enrich_group(entity_id: UUID, created_at, container) -> dict[str, Any] | None:
    group = container.group_claim_repo.get_by_id(entity_id)
    if group is None:
        return None
    member_count = sum(1 for c in container.claim_repo.get_all() if c.group_id == group.group_id)
    return {
        "entity_id": str(entity_id),
        "entity_type": "group_claim",
        "category": "Grupo",
        "created_at": created_at,
        "info_fields": {
            "Nombre": group.name,
            "Gestiones": str(member_count),
        },
    }
```

**Design notes:**
- Each function returns `None` if entity was deleted — caller skips `None` rows
- `info_fields` is a dict consumed by table rendering for category-specific columns
- `category` is used for colored badge ("Factura"=blue, "Gestión"=orange, "Grupo"=green)

**Files:**
- `src/ui/pages/documentos.py`

**Dependencies:** 1.1 (protocol must declare `get_document_entities`)

**Completion criteria:**
- [ ] Three enrichment functions: `_enrich_invoice`, `_enrich_claim`, `_enrich_group`
- [ ] `_enrich_entity` dispatches correctly by `entity_type`
- [ ] Missing/deleted entities return `None` (graceful degradation)
- [ ] Each result dict has correct structure for table rendering

---

## Group 2 — Category View (expandable sections)

### Task 2.1 — Build category grouping logic and expandable sections

**What:** Implement a `@ui.refreshable` function `_render_category_view()` inside `documentos_page()` that:
1. Calls `container.document_repo.get_all()`
2. For each doc, calls `container.document_repo.get_document_entities(doc.document_id)`
3. Groups entity links by `entity_type` using a dict-of-dicts for dedup
4. Renders 3 `ui.expansion()` sections: "Gestiones (N)", "Facturas (N)", "Grupos (N)"
5. Lists document rows inside each section, clickable to set selection

**Grouping pattern:**
```python
from collections import defaultdict
category_map: dict[str, dict[UUID, Document]] = defaultdict(dict)
for doc in docs:
    entities = container.document_repo.get_document_entities(doc.document_id)
    for ent in entities:
        category_map[ent["entity_type"]][doc.document_id] = doc
```

**Rendering order:** "Gestiones" (claim), "Facturas" (invoice), "Grupos" (group_claim).

**Section content:**
- Header: `ui.expansion(f"Gestiones ({count})", icon="...")`
- Inside: document rows with name, type, size, date (simpler than existing table but same info)
- Each row: `on_click=lambda doc_id=d.document_id: _select_document(doc_id)`
- If count == 0: show `ui.label("Sin documentos en esta categoría.").classes("text-gray-400 italic")`

**Wire to selection state** (shared with Group 3):
```python
selected_doc_id: UUID | None = None
selected_entities: list[dict[str, Any]] = []
```

**Files:**
- `src/ui/pages/documentos.py` (inside `documentos_page`)

**Dependencies:** 1.1 (protocol)

**Completion criteria:**
- [ ] Category view shows three expandable sections with correct entity counts
- [ ] Documents linked to multiple entity types appear in each relevant section
- [ ] Empty categories show empty-state message
- [ ] Clicking a document row updates selection state
- [ ] Documents deduplicated within each category

---

### Task 2.2 — Selection state management and visual highlighting

**What:** Implement `_select_document()` function and wire it so that:
- Clicking a doc row in category view (or list view) selects it
- Clicking the same doc again deselects it (toggle)
- Selected doc is visually highlighted (background color change)
- List view must also support row click → selection (add click handler to existing table)

**Selection handler:**
```python
def _select_document(doc_id: UUID | None) -> None:
    nonlocal selected_doc_id, selected_entities
    if selected_doc_id == doc_id:
        selected_doc_id = None
        selected_entities = []
    else:
        selected_doc_id = doc_id
        links = container.document_repo.get_document_entities(doc_id)
        selected_entities = list(links or [])
    _render_related_entities.refresh()
    _render_category_view.refresh()  # re-highlight
```

**List view integration:** The existing `ui.table` needs a click handler on rows. Use `table.on("row-click", ...)` Quasar event:
```python
def handle_row_click(e) -> None:
    doc_id = UUID(e.args["row"]["document_id"])
    _select_document(doc_id)

table.on("row-click", handle_row_click)
```

**Visual highlighting:**
- In category view: use conditional class `bg-blue-100` or `bg-primary-100` when `doc.document_id == selected_doc_id`
- In list view: use `selected-row` prop or custom slot styling

**Files:**
- `src/ui/pages/documentos.py`

**Dependencies:** 2.1

**Completion criteria:**
- [ ] Click toggles selection (same click = deselect)
- [ ] Selected doc highlighted in both views
- [ ] `selected_entities` populated on selection change
- [ ] Existing list view row-click doesn't interfere with download button

---

## Group 3 — Related-Entities Table

### Task 3.1 — Build the related-entities table component

**What:** Implement `_render_related_entities()` as a `@ui.refreshable` inside `documentos_page()` that shows a master-detail table above both views displaying entities linked to the selected document.

**Table columns:**

| Column | Content |
|--------|---------|
| Documento | `selected_doc.name` |
| Categoría | Colored badge via `ui.badge` |
| Vinculado | `created_at` formatted as `%d/%m/%Y` |
| Detalle | Category-specific info (built from `info_fields`) |

**Color mapping:**
```python
badge_colors = {"Factura": "blue", "Gestión": "orange", "Grupo": "green"}
```

**States:**
- `selected_doc_id is None`: "Seleccioná un documento para ver sus entidades vinculadas."
- `selected_doc_id set but selected_entities empty`: "Sin entidades vinculadas a este documento."
- Normal: render table with enriched rows

**Enrichment on refresh:**
```python
def _render_related_entities() -> None:
    if selected_doc_id is None:
        ui.label("Seleccioná un documento para ver sus entidades vinculadas.").classes("text-gray-400 italic")
        return
    selected_doc = next((d for d in container.document_repo.get_all() if d.document_id == selected_doc_id), None)
    if not selected_entities:
        ui.label("Sin entidades vinculadas a este documento.").classes("text-gray-400 italic")
        return
    enriched = [_enrich_entity(e, container) for e in selected_entities]
    enriched = [r for r in enriched if r is not None]
    # Build detail string from info_fields
    for row in enriched:
        row["detail"] = " | ".join(f"{k}: {v}" for k, v in row["info_fields"].items())
    # Render table
    columns = [
        {"name": "doc_name", "label": "Documento", "field": "doc_name", "align": "left"},
        {"name": "category", "label": "Categoría", "field": "category", "align": "left"},
        {"name": "created_at", "label": "Vinculado", "field": "created_at", "align": "left"},
        {"name": "detail", "label": "Detalle", "field": "detail", "align": "left"},
    ]
    rows = [
        {
            "doc_name": selected_doc.name if selected_doc else "—",
            "category": r["category"],
            "created_at": r["created_at"].strftime("%d/%m/%Y") if r.get("created_at") else "—",
            "detail": r["detail"],
            "entity_type": r["entity_type"],
            "entity_id": r["entity_id"],
        }
        for r in enriched
    ]
    ui.table(columns=columns, rows=rows, row_key="entity_id").classes("w-full mb-4").on(
        "row-click", lambda e: _open_entity(
            e.args["row"]["entity_type"], UUID(e.args["row"]["entity_id"]), container
        )
    )
```

**Note:** The `_open_entity` function is defined in Task 3.2. For apply ordering, this task's `_render_related_entities` can be written to reference it before it exists — but logically it's built together or after.

**Files:**
- `src/ui/pages/documentos.py`

**Dependencies:** 1.1, 1.3, 2.2

**Completion criteria:**
- [ ] Table visible above both views, positioned between toggle and content area
- [ ] Empty/disabled states render correctly
- [ ] Each row shows correct category badge with appropriate color
- [ ] Category-specific detail rendered as formatted string
- [ ] Table reacts to selection changes (via refresh)

---

### Task 3.2 — Implement entity navigation dispatch (`_open_entity`)

**What:** Write a module-level function `_open_entity(entity_type: str, entity_id: UUID, container: Container)` that dispatches click events to the correct dialog or detail page.

**Logic:**
```python
def _open_entity(entity_type: str, entity_id: UUID, container: Container) -> None:
    if entity_type == "invoice":
        from src.ui.pages.facturacion import _invoice_dialog
        invoice = container.billing_repo.get_by_id(entity_id)
        if invoice:
            _invoice_dialog(invoice, refresh_fn=lambda: None)
    elif entity_type == "group_claim":
        from src.ui.pages.grupos import _edit_group_dialog
        group = container.group_claim_repo.get_by_id(entity_id)
        if group:
            _edit_group_dialog(group, container, refresh_fn=lambda: None)
    elif entity_type == "claim":
        ui.navigate.to(f"/gestiones/{entity_id}")
```

**Key constraints:**
- Deferred imports (`from src.ui.pages.facturacion import _invoice_dialog`) avoid circular imports at module load time
- `_edit_group_dialog` is the module-level function extracted in Task 1.2
- Claim navigation is a full page navigation (`ui.navigate.to`), not a dialog
- Silently no-op if entity is not found (graceful degradation)

**Wired from Task 3.1:** The related-entities table fires `row-click` which calls this function.

**Files:**
- `src/ui/pages/documentos.py` (module level)

**Dependencies:** 1.2 (extracted `_edit_group_dialog`)

**Completion criteria:**
- [ ] Invoice row click opens existing invoice dialog from `facturacion.py`
- [ ] Group row click opens existing group edit dialog from `grupos.py`
- [ ] Claim row click navigates to `/gestiones/{id}`
- [ ] No circular import errors

---

## Group 4 — Toggle + Integration

### Task 4.1 — Add view toggle with reactive state

**What:** Add a `ui.toggle` between List View and Category View that controls which refreshable renders. Add reactive state variables and the toggle switch component.

**State variables (inside `documentos_page`):**
```python
view_mode: str = "lista"  # "lista" | "categorias"
```

**Toggle component** (placed between page title and content area):
```python
with ui.row().classes("items-center gap-4 mb-4"):
    ui.toggle(["Lista", "Categorías"], on_change=lambda: _render_view.refresh()).bind_value(
        globals(), "view_mode"
    )
```

**Note:** `bind_value` to `globals()` works for string variables in the closure scope. Alternative: use a `ui.refreshable` wrapper that reads `view_mode` and delegates to the correct view.

**Decision:** Use a wrapper refreshable `_render_view()` that conditionally renders:
```python
@ui.refreshable
def _render_view() -> None:
    if view_mode == "categorias":
        _render_category_view()
    else:
        # Render existing list view content — extract to refreshable too
        _render_list_view()
```

**Refactor existing list view:** Extract the existing table UI (lines 25-105 in current `documentos.py`) into `_render_list_view()` refreshable.

**Files:**
- `src/ui/pages/documentos.py`

**Dependencies:** None (can be done early, defines the layout shell)

**Completion criteria:**
- [ ] Toggle renders between page title and content
- [ ] Defaults to "Lista" (existing view)
- [ ] Switching toggles visibility without page reload
- [ ] `view_mode` state is tracked reactively

---

### Task 4.2 — Wire up full page layout and final integration

**What:** Reorganize `documentos_page()` so the component tree matches the design:

```
AppShell
  ├── ui.label("Documentos")
  ├── ui.toggle(["Lista", "Categorías"])
  ├── _render_related_entities()    ← always visible
  └── _render_view()                ← switches between views
     ├── _render_list_view()
     └── _render_category_view()
```

**Concrete layout changes in `documentos_page()`:**

1. Move imports: add `from collections import defaultdict`, `from typing import Any, Callable`
2. Declare state: `view_mode`, `selected_doc_id`, `selected_entities`
3. Place toggle
4. Place `_render_related_entities()` — always rendered (refreshes internally)
5. Place `_render_view()` wrapper (delegates to correct view)
6. Define all refreshable functions as inner functions of `documentos_page()`
7. Ensure `_open_entity` and enrichment helpers stay at module level (outside the page function)

**Existing code preservation:**
- The existing `_format_size` helper stays at module level
- The existing `handle_download` function moves into `_render_list_view()` refreshable
- The existing `register_documentos_page` function structure stays the same

**Files:**
- `src/ui/pages/documentos.py`

**Dependencies:** All previous tasks

**Completion criteria:**
- [ ] Full component tree matches design
- [ ] Toggle works: switches between list and category view
- [ ] Related-entities table persists above both views
- [ ] Document selection works from both views
- [ ] Entity navigation opens correct dialogs/pages
- [ ] Existing list view + download behavior unchanged
- [ ] No page reload on view switch or document select

---

## Apply Order

The tasks should be applied in this strict order — each depends on the previous:

1. **1.1** — protocol change (independent)
2. **1.2** — extract `_edit_group_dialog` (independent of 1.1)
3. **1.3** — enrichment helpers (depends on 1.1 for conceptual correctness, can start after 1.1)
4. **4.1** — toggle + layout refactor (no code dependency on 1.x, can run in parallel)
5. **2.1** — category view (depends on 1.1, 4.1 for layout)
6. **2.2** — selection state + highlighting (depends on 2.1, 4.1)
7. **3.1** — related-entities table (depends on 1.1, 1.3, 2.2, 4.1)
8. **3.2** — entity navigation (depends on 1.2)
9. **4.2** — final integration (depends on everything)

**Parallel-friendly batches:**
- Batch A (parallel): 1.1, 1.2, 4.1
- Batch B (after A): 1.3
- Batch C (after B): 2.1
- Batch D (sequential): 2.2 → 3.1 → 3.2
- Batch E (after D): 4.2

## Notes for the Apply Phase

- `src/domain/ports/repositories.py` needs `from typing import Any` (already present) and the method signature added at line ~138
- `container.py` needs no changes — repos are already exposed via properties
- The `_render_list_view` extraction should keep the existing `sorted(docs, key=lambda d: d.created_at, reverse=True)` behavior
- The category view should NOT fetch enriched details — only raw entity links to group docs. Enrichment is lazy (only for selected document)
- Empty string join for detail column uses `" | "` separator
- The `ui.toggle` `bind_value` might need a helper dict or `value` prop instead — verify during apply
- Test with both real and in-memory repositories
