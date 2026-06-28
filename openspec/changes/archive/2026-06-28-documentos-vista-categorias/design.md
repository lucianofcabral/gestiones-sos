# Design: Document Category View

## Technical Approach

Single-page enhancement to `documentos.py`: add a view toggle, category-based document grouping, and a master-detail related-entities table that invokes existing entity dialogs. The `DocumentRepoPort` protocol gains `get_document_entities()`. The nested `_edit_group` in `grupos.py` is extracted to module level so it can be imported.

## Architecture Decisions

### Decision: Toggle mechanism
| Option | Tradeoff | Decision |
|--------|----------|----------|
| `ui.toggle` + `@ui.refreshable` | Familiar project pattern, zero-dependency | **Adopt** |
| Vue route params | Over-engineered for one toggle | Rejected |
| Separate pages | Duplicates shell/nav | Rejected |

### Decision: Group edit dialog reuse
| Option | Tradeoff | Decision |
|--------|----------|----------|
| Extract `_edit_group` to module-level in `grupos.py` | +10 lines refactor, clean import | **Adopt** |
| `ui.navigate.to("/grupos")` | Loses user context on documentos page | Rejected |
| Duplicate dialog in documentos.py | DRY violation, maintenance burden | Rejected |

### Decision: Entity enrichment strategy
| Option | Tradeoff | Decision |
|--------|----------|----------|
| **Lazy**: enrich only selected document | One round of repo lookups per click | **Adopt** — matches N+1 risk in proposal |
| Batch enrich for category view | Pre-fetches all entity details at page load | Rejected — O(n*m) queries upfront |
| New use case `GetDocumentEntitiesWithDetail` | Clean architecture but adds abstraction layer | Rejected — MVP scope, no reuse elsewhere |

### Decision: Category view grouping
| Option | Tradeoff | Decision |
|--------|----------|----------|
| **N+1**: `get_all()` then per-doc `get_document_entities()` | Simple, predictable, 1+N queries | **Adopt** — acceptable for typical doc count (<100) |
| New `get_all_document_entities()` method | One query but new protocol method | Rejected — scope creep for MVP |

## Data Flow

```
Page load
  │
  ├── container.document_repo.get_all()          → documents[]
  │
  ├── [List View] ui.table(rows=documents)
  │     └── row click → set selected_doc_id
  │
  ├── [Category View]
  │     └── for doc in documents:
  │           └── get_document_entities(doc.id)  → entities[]
  │                 └── group by entity_type → {gestiones:[], facturas:[], grupos:[]}
  │                       └── ui.expansion per type → doc rows with entity count
  │                             └── doc click → set selected_doc_id
  │
  └── [Related-Entities Table] (above both views)
        └── selected_doc_id changes → get_document_entities(doc_id)
              └── for each entity:
                    ├── "invoice"   → billing_repo.get_by_id(id) → Invoice
                    ├── "claim"     → claim_repo.get_by_id(id)   → Claim
                    │                 └── sos_claim_repo.get_claims_by_claim_id(id)
                    │                 └── claim_kind_repo.get_by_id(claim.claim_kind_id)
                    └── "group_claim" → group_claim_repo.get_by_id(id) → GroupClaim
                                         └── count claims where group_id == id
                          └── enrich + render table row
                                └── row click → dispatch navigation/dialog
```

## File Changes

| File | Action | Description |
|------|--------|-------------|
| `src/domain/ports/repositories.py` | Modify | Add `get_document_entities(document_id: UUID) -> list[dict]` to `DocumentRepoPort` |
| `src/ui/pages/grupos.py` | Modify | Extract `_edit_group(group, container)` to module level for import |
| `src/ui/pages/documentos.py` | Modify | Add toggle, category view, selection state, related-entities table, entity navigation |

## Interfaces / Contracts

### DocumentRepoPort addition

```python
# src/domain/ports/repositories.py — add to DocumentRepoPort
def get_document_entities(self, document_id: UUID) -> list[dict[str, Any]]: ...
```

Returns `[{"document_id": UUID, "entity_type": str, "entity_id": UUID, "created_at": datetime}, ...]` — already implemented in `SqlAlchemyDocumentRepository`.

### Extracted group dialog

```python
# src/ui/pages/grupos.py — module-level, extracted from nested _edit_group
def _edit_group_dialog(group: GroupClaim, container: Container) -> None:
    """Open the group edit dialog. Extracted for reuse from documentos.py."""
    ...  # existing dialog body (members, documents, save/cancel)
```

### Related-entity row dispatch

```python
def _open_entity(entity_type: str, entity_id: UUID) -> None:
    if entity_type == "invoice":
        from src.ui.pages.facturacion import _invoice_dialog
        invoice = container.billing_repo.get_by_id(entity_id)
        _invoice_dialog(invoice, refresh_fn=lambda: None)
    elif entity_type == "group_claim":
        from src.ui.pages.grupos import _edit_group_dialog
        group = container.group_claim_repo.get_by_id(entity_id)
        _edit_group_dialog(group, container)
    elif entity_type == "claim":
        ui.navigate.to(f"/gestiones/{entity_id}")
```

## UI Component Tree

```
AppShell
  ├── ui.label("Documentos")
  ├── ui.toggle(["Lista", "Categorías"])     ← view mode switcher
  │
  ├── [Related-Entities Table]                ← always visible
  │     └── ui.table(columns=[doc_name, category badge, category fields])
  │           └── row click → _open_entity()
  │
  ├── [List View - @ui.refreshable]
  │     └── ui.table(columns=existing) + download slot
  │
  └── [Category View - @ui.refreshable]
        └── ui.expansion("Gestiones (N)")
        │     └── document rows (clickable → select)
        ├── ui.expansion("Facturas (N)")
        │     └── document rows (clickable → select)
        └── ui.expansion("Grupos (N)")
              └── document rows (clickable → select)
```

## State Management

| Variable | Type | Initial | Purpose |
|----------|------|---------|---------|
| `view_mode` | str | `"lista"` | Controls which refreshable renders |
| `selected_doc_id` | UUID\|None | `None` | Currently selected document |
| `selected_entities` | list[dict] | `[]` | Enriched entity rows for the table |

State lives as closures inside `documentos_page()` — matches existing project patterns (see `facturacion.py`, `grupos.py`).

## Category-specific Info Rendering

| Entity Type | Repo Query | Display Fields |
|-------------|------------|----------------|
| `invoice` | `billing_repo.get_by_id(id)` → Invoice + `period_repo.get_by_id(inv.period_id)` | invoice_number, period.period_name |
| `claim` | `claim_repo.get_by_id(id)` → Claim + `claim_kind_repo.get_by_id(claim.claim_kind_id)` → ClaimKind + `sos_claim_repo.get_claims_by_claim_id(claim.claim_id)` → SosClaim | tipo (ClaimKind.name), número (SosClaim.gestion), patente (Claim.plate), póliza (Claim.policy_number), cliente (Claim.claimer_name) |
| `group_claim` | `group_claim_repo.get_by_id(id)` → GroupClaim | name, member_count (filter claims by group_id) |

Color badges: Factura=blue, Gestión=orange, Grupo=green (via `ui.badge`).

## Testing Strategy

| Layer | What to Test | Approach |
|-------|-------------|----------|
| Unit | `get_document_entities` protocol conformance | Protocol check on adapter |
| Unit | Entity enrichment helpers | Pure function tests |
| Integration | Toggle switches view correctly | Page render → assert expansion visible |
| Integration | Related-entities table populates on selection | Mock repo, click doc, assert table rows |
| E2E | Full flow: toggle → category view → select doc → entity table → click opens dialog | Browser test (future) |

## Migration / Rollout

No migration required. Toggle defaults to "Lista" — existing users see no change until they toggle.

## Open Questions

None.

## Delivery Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | ~220–300 |
| 400-line budget risk | Low |
| Chained PRs recommended | No |
