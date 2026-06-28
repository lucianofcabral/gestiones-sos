# Design: Mejoras Tablas Pagos Acciones

## Technical Approach

Six independent UI/UX enhancements on top of the existing row-based table pattern (`ui.row()` + `ui.label()`, NO `ui.table()`). Each feature has its own scope, code paths, and revertibility. Backend changes are additive (new DTO fields, no column migrations). All payments are in-memory loaded (no pagination), so payment-count queries are O(1) per page load.

## Architecture Decisions

### 1. Auto-fit Table Columns

**Choice**: Replace fixed `w-*` on content columns with `flex-1` + `truncate`; keep action/status columns at fixed widths.
**Rationale**: Content columns (claimer_name, policy_number, description) benefit from elastic space. Status/action columns (active badge, delete button) are always small. The `gap-2` on the parent row already provides spacing — `flex-1` distributes remaining space proportionally.
**Per-table strategy**:

| Table | Content col(s) → `flex-1` | Fixed cols retained |
|---|---|---|
| `gestiones.py` | Asegurado, Gestión/Ref., Póliza, Patente | Tipo(w-20), Monto(w-28), Fecha(w-28), Resuelto(w-16), ""(w-10) |
| `gestiones_nueva.py` grouped | Asegurado | Póliza(w-24), Patente(w-20), Monto(w-24), ""(w-10) |
| `gestiones_detalle.py` payments | Pagador, Benef. | Monto(w-28), Fecha(w-28), Activo(w-16), ""(w-20) |
| `gestiones_detalle.py` docs | Nombre | Tipo(w-20), Tamaño(w-20), Fecha(w-28), ""(w-24) |
| `documentos.py` list | Nombre | Tipo(w-20), Tamaño(w-20), MIME(w-28), Fecha(w-24), ""(w-16) |
| `pagos.py` | Cliente, Dominio, Póliza | Monto(w-24), Pagador(w-24), Medio(w-20), Benef.(w-24), Tipo(w-20), Grupo(w-20), Gestión(w-20), Fecha(w-24), NC(w-20), Activo(w-14), Acciones(w-36) |
| `facturacion.py` | Descripción | Número(w-28), Fecha(w-24), Monto(w-24), Activo(w-16), ""(w-24) |
| `grupos.py` | Nombre, Descripción | Creado(w-24), Gestiones(w-16), Monto Total(w-28), Acciones(w-28) |

### 2. Inactive Row Highlighting

**Choice**: CSS class `opacity-50` on the row's `ui.row()` when entity `active == False`.
**Rationale**: Lightest touch — no backend changes, no new CSS. The row remains clickable and interactive. `opacity-50` halves the visual weight without hiding content.
**Per-table detection**:

| Table | Field | Condition |
|---|---|---|
| `gestiones.py` | `g.active` | `active == False` |
| `gestiones_nueva.py` (grouped table) | N/A | No active field in local state |
| `gestiones_detalle.py` payments | `pmt.active` | `active == False` |
| `documentos.py` | N/A | Documents have no active field |
| `pagos.py` | `p.active` | `active == False` |
| `facturacion.py` | `inv.active` | `active == False` |
| `grupos.py` | `g.active` | `active == False` |

### 3. Document Type Column

**Choice**: Query `document_entities` per document row; show primary entity type as a human label; comma-separated for multiple entities.
**Choice**: Add `get_document_entity_types(document_id) -> list[str]` to `DocumentRepoPort` and implement in `SqlAlchemyDocumentRepository`.
**Rationale**: The existing `get_document_entities` already returns entity data. A thin wrapper returning just the types is trivial. The label mapping uses existing `_CATEGORY_LABELS` from `documentos.py` (claim → "Gestiones", invoice → "Facturas", group_claim → "Grupos").
**Impact**: Only `documentos.py` — the `doc.type` is always "documento". Replace with entity type labels. No spec change needed since `DocumentEntity.entity_type` already stores canonical values.

### 4. Payment Auto-generation on Grouped Claim Creation

**Choice**: Checkbox in `_render_grouped_card` of `gestiones_nueva.py`; batch loop in `_on_submit_all` after claims are created.
**Choice**: Reuse `RegistrarPagoUseCase` directly; replicate the logic from `grupos.py:_generar_pagos` (payer=SM, payee=prestador, via=transferencia, amount=claimed_amount).
**Choice**: Do NOT auto-solve claims. The checkbox label says "Generar pagos automáticamente" — payment creation only.
**Rationale**: Auto-solving couples payment creation to claim status. Leave `solved=False` so the user can review. The agent lookups (`get_sm()`, `get_prestador()`, `get_transferencia()`) are O(1) cached queries.
**Flow**:

```
_on_submit_all()
  → creates all claims (existing)
  → if checkbox checked:
       for each claim_row:
         RegistrarPagoUseCase.execute(
           claim_id, payer=SM, payee=prestador, via=transferencia, amount=claimed_amount
         )
  → dialog.close()
```

### 5. Payment Count Column

**Choice**: Add `payment_count: int = 0` to `GestionDTO`. Compute in `ObtenerGestionesUseCase.execute()`.
**Choice**: Count payments from the in-memory `payment_repo.get_all()` result, which is already loaded for filtering in `gestiones.py`.
**Rationale**: The use case already loads all claims and all payments are fetched in the UI layer. Counting is `sum(1 for p in all_payments if p.claim_id == claim.claim_id)` — O(N) over claims, no extra queries.
**Column position**: After "Resuelto", before the empty action column. Fixed width `w-16` (icon + number fits in 16).

### 6. Action Icons

**Choice**: Compact icon-only `ui.button` row per gestion row: edit claim, edit group, unlink group, add payment, credit note.
**Choice**: No dropdown — 5 icons fit in the row at 1280px+ with `dense round size=sm` props. Each icon opens its respective dialog.
**Choice**: Extract reusable dialogs from `gestiones_detalle.py`:

| Dialog | Extract from | Signature |
|---|---|---|
| `pago_dialog` | `_pago_dialog` (existing) | `(container, claim_id, payment, on_save, agent_options, via_options, nc_via_id, sos_id, sm_id) → None` |
| `credito_dialog` | New variant of `_pago_dialog` | Locks payer=SOS, payee=SM, medio=NC; calls `RegistrarPagoUseCase` |
| `edit_claim_dialog` | `_guardar_cambios` logic from detail page | `(container, claim_id, on_success) → None` (new dialog) |
| `edit_group_dialog` | Already extracted in `grupos.py` | Reuse as-is |
| `unlink_group_flow` | `_remove_claim_dialog` from `grupos.py` | `(container, claim_id, on_success) → None` |

**Action column**: Fixed `w-40` (5 icons × ~8px each + gap).

### 7. DTO and Use Case Changes

```python
# GestionDTO — new fields
class GestionDTO(BaseModel):
    # ... existing fields ...
    group_id: UUID | None = None
    payment_count: int = 0
```

`ObtenerGestionesUseCase`: populate `group_id` from `claim.group_id`, `payment_count` by iterating `payment_repo.get_all()`.

### 8. Component Extraction

```python
def pago_dialog(
    container: Container,
    claim_id: UUID,
    payment: Payment | None,
    on_save: Callable,
    agent_options: dict[str, str],
    via_options: dict[str, str],
    nc_via_id: str | None,
    sos_id: str | None,
    sm_id: str | None,
) -> None:
    """Create or edit a payment. Extracted from gestiones_detalle.py _pago_dialog."""
    ...

def credito_dialog(
    container: Container,
    claim_id: UUID,
    on_save: Callable,
    agent_options: dict[str, str],
    via_options: dict[str, str],
    nc_via_id: str,
    sos_id: str,
    sm_id: str,
) -> None:
    """NC-only payment dialog: locked payer=SOS, payee=SM, medio=NC."""
    ...
```

## Data Flow

```
UI Layer (gestiones.py)
  │
  ├─ ObtenerGestionesUseCase ──→ GestionDTO[payment_count, group_id]
  │
  ├─ Action icons ──→ pago_dialog() / credito_dialog() / edit_group_dialog() / ...
  │                    └─ RegistrarPagoUseCase / ActualizarGestion / ...
  │
  └─ Inactive row ──→ CSS class `opacity-50` on `active==False`

Doc Type (documentos.py)
  └─ get_document_entity_types(document_id) ──→ _CATEGORY_LABELS mapping

Auto-generation (gestiones_nueva.py)
  └─ checkbox → loop: RegistrarPagoUseCase(payer=SM, payee=prestador, via=transferencia)
```

## File Changes

| File | Action | Description |
|---|---|---|
| `src/domain/models/entities.py` | Modify | Add `group_id` and `payment_count` to `GestionDTO` |
| `src/application/use_cases/claims/obtener_gestiones.py` | Modify | Populate `group_id` + `payment_count` |
| `src/domain/ports/repositories.py` | Modify | Add `get_document_entity_types()` to `DocumentRepoPort` |
| `src/adapters/persistence/sqlalchemy_document_repository.py` | Modify | Implement `get_document_entity_types()` |
| `src/adapters/persistence/inmemory_document_repository.py` | Modify | Implement stub `get_document_entity_types()` |
| `src/ui/pages/gestiones.py` | Modify | Auto-fit cols, inactive rows, payment_count col, action icons |
| `src/ui/pages/gestiones_nueva.py` | Modify | Auto-generate payment checkbox |
| `src/ui/pages/gestiones_detalle.py` | Modify | Extract `pago_dialog`, `credito_dialog` to shared module |
| `src/ui/pages/documentos.py` | Modify | Entity type col + auto-fit |
| `src/ui/pages/pagos.py` | Modify | Auto-fit cols + inactive rows |
| `src/ui/pages/facturacion.py` | Modify | Auto-fit cols + inactive rows |
| `src/ui/pages/grupos.py` | Modify | Auto-fit cols + inactive rows |
| `src/ui/pages/periodos.py` | Modify | Auto-fit cols + inactive rows |
| `src/ui/dialogs/__init__.py` | Create | Shared dialog functions |
| `src/ui/dialogs/pago_dialog.py` | Create | Extracted `pago_dialog` + `credito_dialog` |
| `src/ui/dialogs/edit_claim_dialog.py` | Create | Edit claim dialog (new) |

## Interfaces / Contracts

```python
# DocumentRepoPort addition
def get_document_entity_types(self, document_id: UUID) -> list[str]: ...

# New shared location
# src/ui/dialogs/__init__.py — exports:
def pago_dialog(...) -> None: ...
def credito_dialog(...) -> None: ...
def edit_claim_dialog(...) -> None: ...

# GestionDTO changes
class GestionDTO(BaseModel):
    # ... existing ...
    group_id: UUID | None = None
    payment_count: int = 0
```

## Testing Strategy

| Layer | What to Test | Approach |
|---|---|---|
| Unit | Payment count computation | Mock payment_repo.get_all(), assert DTO field |
| Unit | Auto-generation logic | Unit test `_on_submit_all` with checkbox on/off |
| Integration | Document entity types | Test against DB fixture with known document_entities |
| E2E | Auto-fit rendering | Visual check at 1280px (manual, no screenshot testing infra) |
| E2E | Action icon dialogs | Manual — click each icon, verify dialog opens |

## Migration / Rollout

No migration required. All changes are additive to DTOs and UI. Rollback per feature (see proposal rollback plan).

## Open Questions

- [ ] Prestador agent name: `get_prestador()` — confirm this is the correct payee for auto-generation (it's used in `grupos.py:_generar_pagos`).
- [ ] Should auto-generation also mark claims as `solved=True`? The design says NO, but needs team confirmation.
- [ ] Payment count: should we exclude inactive payments from the count? Current proposal says raw count.
