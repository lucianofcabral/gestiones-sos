# Delta Spec: Mejoras Tablas Pagos Acciones

## Overview

Six UI/UX enhancements across the platform's table-based pages: auto-fit column widths, inactive-row highlighting, real document entity types, payment-generation checkbox on Tres Arroyos creation, payment-count column in gestiones list, and inline action icons per gestion row. All changes are frontend-only except the `payment_count` DTO addition.

---

## ADDED Requirements

### Domain: claim-listing — Payment Count Column

#### Requirement: Payment count column in gestiones table

The `/gestiones` table SHALL include a "Cant. Pagos" column after the "Monto" column. The value SHALL be the count of `Payment` records for that `claim_id` (zero if none).

The `GestionDTO` SHALL gain a `payment_count: int = 0` field. The `ObtenerGestiones` use case SHALL compute payment counts via a single aggregate query (e.g., `COUNT` grouped by `claim_id`) or by loading all payments once and counting in memory, to avoid N+1.

**Scenario: Payment count renders for rows with payments**

- GIVEN claim A has 3 payments and claim B has 0 payments
- WHEN the user views `/gestiones`
- THEN claim A's row SHALL show "3" in the "Cant. Pagos" column
- AND claim B's row SHALL show "0" in the "Cant. Pagos" column

**Scenario: Sort by payment count**

- GIVEN the table has multiple claims with varying payment counts
- WHEN the user clicks the "Cant. Pagos" column header
- THEN the table SHALL sort by payment count ascending; clicking again SHALL reverse

**Scenario: Payment count column header**

- GIVEN the user navigates to `/gestiones`
- THEN the column header SHALL read "Cant. Pagos"
- AND the column width SHALL be compact (no truncation needed for single-digit counts)

---

### Domain: claim-listing — Action Icons

#### Requirement: Inline action icons per gestion row

Each row in the `/gestiones` table SHALL display an action cell with icons. The actions SHALL be grouped in a compact dropdown menu (e.g., `ui.button` with `icon="more_vert"` opening a `ui.menu`) to avoid cluttering the row with 5+ individual icons.

The action icons SHALL be:

| Action | Condition | Behavior |
|--------|-----------|----------|
| Edit claim | Always | Navigate to `/gestiones/{claim_id}` (same as row click) |
| Edit group | `group_id` is set | Open `edit_group_dialog` from `grupos.py` |
| Unlink group | `group_id` is set | Call `ActualizarGrupoDeGestion` with `new_group_id=None`, refresh table |
| Add payment | Always | Open `_pago_dialog` from `gestiones_detalle.py` (extracted for reuse) |
| Credit note | Has NC → open NC edit/delete; No NC → open locked NC dialog | See NC requirement below |

**Scenario: Action menu renders for every row**

- GIVEN the user is viewing `/gestiones`
- THEN each row SHALL show a "more_vert" icon at the right end
- AND clicking it SHALL open a dropdown menu with available actions

**Scenario: Edit group icon visible only for grouped claims**

- GIVEN a row has `group_id` set
- WHEN the user opens the action menu
- THEN "Editar grupo" and "Desvincular grupo" SHALL be visible

**Scenario: Unlink group removes claim from group**

- GIVEN a claim belongs to group G
- WHEN the user clicks "Desvincular grupo" and confirms
- THEN `ActualizarGrupoDeGestion(claim_id, new_group_id=None)` SHALL execute
- AND the table SHALL refresh

**Scenario: Add payment opens payment dialog**

- GIVEN the user clicks "Agregar pago" in the action menu
- THEN the `_pago_dialog` SHALL open with the claim_id pre-filled to the current row's claim
- AND a successful save SHALL refresh the table

**Scenario: No group actions when ungrouped**

- GIVEN a row has `group_id` = None
- WHEN the user opens the action menu
- THEN "Editar grupo" and "Desvincular grupo" SHALL NOT appear

#### Requirement: Credit note action

For the credit note action, the system SHALL check if the claim already has a NC payment. If yes, the action SHALL open a dialog to edit or delete the existing NC. If no NC exists, the action SHALL open a "locked" NC creation dialog (same as existing, but with payer/payee/via pre-filled and locked).

**Scenario: Claim with NC — open edit/delete dialog**

- GIVEN a claim has an existing NC payment
- WHEN the user clicks "Nota de Crédito" in the action menu
- THEN the system SHALL open the existing NC edit dialog showing current values
- AND the user SHALL be able to edit or delete the NC

**Scenario: Claim without NC — open locked creation dialog**

- GIVEN a claim has no NC payment
- WHEN the user clicks "Nota de Crédito" in the action menu
- THEN the system SHALL open an NC creation dialog with payer/payee/via pre-filled and locked
- AND the user SHALL only be able to set the amount

---

### Domain: claim-listing — Inactive Row Highlighting

#### Requirement: Visual distinction for inactive rows in gestiones

The system SHALL apply a visual style to rows where `GestionDTO.active == False`. The style SHALL use reduced opacity (`opacity-50` or equivalent) and muted text color to distinguish inactive claims.

**Scenario: Inactive row appears dimmed**

- GIVEN the user has enabled "Mostrar inactivos"
- WHEN the table renders an inactive claim
- THEN that row SHALL have reduced opacity (e.g., `opacity-50`) compared to active rows
- AND the row SHALL remain clickable and interactive

**Scenario: Active row unaffected**

- GIVEN the user is viewing the table
- WHEN an active claim renders
- THEN its appearance SHALL NOT be affected by the inactive styling

---

### Domain: document-gallery — Entity Type Column

#### Requirement: Show entity type instead of "documento"

The "Tipo" column in the `/documentos` list view SHALL display the document's entity type from the `document_entities` table instead of the hardcoded `doc.type` value (which is always "documento").

The system SHALL read the first `entity_type` from the document's entity links. Mapping:

| `document_entities.entity_type` | Display value |
|--------------------------------|---------------|
| `claim` | "Gestión" |
| `invoice` | "Factura" |
| `group_claim` | "Grupo" |
| `payment` | "Pago" |
| `credit_note` | "NC" |

**Scenario: Single-entity document shows correct type**

- GIVEN a document is linked to a single claim entity
- WHEN the document renders in the list view
- THEN the "Tipo" column SHALL display "Gestión"

**Scenario: Multi-entity document shows first type with tooltip**

- GIVEN a document is linked to both a claim and an invoice
- WHEN the document renders in the list view
- THEN the "Tipo" column SHALL display the first entity type's display value (e.g., "Gestión")
- AND a tooltip SHALL show all entity types: "Gestión, Factura"

**Scenario: Document with no entity links**

- GIVEN a document has no `document_entities` rows
- WHEN the document renders in the list view
- THEN the "Tipo" column SHALL display "—"

---

### Domain: claim-registration — Auto-Generate Payments Checkbox

#### Requirement: "Generar Pagos" checkbox on Tres Arroyos creation

The `_render_grouped_card` in `/gestiones/nueva` SHALL include a checkbox labeled "Generar pagos automáticamente" below the document upload section. Default value: unchecked.

When checked and the submit succeeds for all claims, the system SHALL invoke the same payment-generation logic as the "Generar Pagos" button in the group edit dialog (`grupos.py:_generar_pagos`): for each created claim, create a payment from SM → Prestador via Transferencia for `claimed_amount`, and set `solved=True`.

**Scenario: Checkbox enabled, claims created with payments**

- GIVEN the agent checks "Generar pagos automáticamente"
- AND the agent submits the form with 3 valid claims
- WHEN all claims are created successfully
- THEN the system SHALL create 3 payments (one per claim, SM→Prestador, Transferencia, amount=claimed_amount)
- AND each claim SHALL be marked as solved
- AND a notification SHALL confirm the count of generated payments

**Scenario: Checkbox disabled, no payments generated**

- GIVEN the agent leaves the checkbox unchecked
- WHEN the agent submits valid claims
- THEN the claims SHALL be created without payments
- AND the claims SHALL NOT be auto-resolved

**Scenario: Payment generation partial failure**

- GIVEN the checkbox is checked and 3 claims are submitted
- WHEN payment for claim 2 fails
- THEN claims 1-3 SHALL still be created
- AND the notification SHALL show "Pagos generados: 2 de 3"
- AND errors SHALL be reported per-claim via `ui.notify`

**Scenario: SM/Prestador/Transferencia not configured**

- GIVEN the checkbox is checked
- WHEN SM, Prestador, or Transferencia entities are missing
- THEN the system SHALL show a warning notification
- AND claims SHALL be created without payments

---

### Domain: claim-detail — Extract Payment/NC Modals for Reuse

#### Requirement: Extract payment dialog for reuse

The `_pago_dialog` function in `gestiones_detalle.py` SHALL be extracted to a shared module (e.g., `src/ui/components/pago_dialog.py`) so it can be invoked from the gestiones list action icons without duplicating logic.

#### Requirement: Extract NC dialog for reuse

The NC creation/edit dialog SHALL be exposed as a reusable function callable from both the detail page and the gestiones list action icons.

---

### Cross-cutting: Auto-fit Table Columns

#### Requirement: Replace fixed widths with auto-fit across all tables

The following tables SHALL replace fixed `w-*` classes with a selective `flex-1` + `truncate` approach. Content columns (text that varies in length) SHALL use `flex-1`. Fixed-width columns (status badges, action buttons, dates, amounts) SHALL keep compact explicit widths.

| File | Table | `flex-1` columns | Keep fixed |
|------|-------|------------------|------------|
| `gestiones.py` | Gestiones list | Asegurado (~w-36 → flex-1) | Tipo (w-20), Gestión/Ref. (w-24), Póliza (w-28), Patente (w-24), Monto (w-28), Fecha (w-28), Resuelto (w-16), Cant. Pagos (w-20), Acciones (w-10) |
| `pagos.py` | Pagos list | Cliente (~w-28 → flex-1) | Monto (w-24), Pagador (w-24), Medio (w-20), Beneficiario (w-24), Tipo (w-20), Grupo (w-20), Dominio (w-24), Póliza (w-24), Gestión (w-20), Fecha (w-24), NC (w-20), Activo (w-14), Acciones (w-36) |
| `documentos.py` | List view | Nombre (~w-36 → flex-1) | Tipo (w-20), Tamaño (w-20), MIME (w-28), Fecha (w-24), "" (w-16) |
| `facturacion.py` | Invoice list | Descripción (~w-48 → flex-1) | Número (w-28), Fecha (w-24), Monto (w-24), Activo (w-16), "" (w-24) |
| `grupos.py` | Groups list | Nombre (~w-36 → flex-1), Descripción (~w-36 → flex-1) | Creado (w-24), Gestiones (w-16), Monto Total (w-28), Acciones (w-28) |
| `periodos.py` | Invoice detail | Descripción (~w-48 → flex-1) | Número (w-28), Fecha (w-24), Importe (w-24), Activo (w-16), "" (w-20) |
| `periodos.py` | NC detail | — (all compact) | ID Pago (w-32), Entregado (w-20), Fecha (w-24), "" (w-20) |
| `gestiones_detalle.py` | Payments table | Pagador (~w-24 → flex-1), Beneficiario (~w-24 → flex-1) | Monto (w-28), Fecha (w-28), Activo (w-16), "" (w-20) |
| `gestiones_nueva.py` | Grouped claims batch | Asegurado (~w-32 → flex-1) | Póliza (w-24), Patente (w-20), Monto (w-24), "" (w-10) |
| `gestiones_detalle.py` | Documents table | Nombre (~w-44 → flex-1) | Tipo (w-20), Tamaño (w-20), Fecha (w-28), "" (w-24) |

**Scenario: Content column expands to fill available width**

- GIVEN a table rendered in a 1280px viewport
- THEN the `flex-1` column(s) SHALL expand to use available horizontal space
- AND fixed-width columns SHALL remain at their specified width

**Scenario: Long text truncates with ellipsis**

- GIVEN a `flex-1` column with text longer than available space
- THEN the text SHALL truncate with an ellipsis (`truncate` class)
- AND a tooltip SHALL show the full text on hover

**Scenario: Header row uses matching widths**

- GIVEN a table with auto-fitted columns
- THEN the header row labels SHALL use the same width classes as the data cells
- AND headers SHALL NOT have `truncate` applied

---

### Cross-cutting: Inactive Row Highlighting

#### Requirement: Apply inactive styling to all `active=False` rows

Every table with an `active` boolean field SHALL apply a visual distinction for inactive rows. The style SHALL be `opacity-50` + `text-gray-500` (or equivalent muted styling) applied at the row level. Active rows SHALL NOT be affected.

Affected tables and their active-field source:

| Page | Active field entity | Detection |
|------|-------------------|-----------|
| `gestiones.py` | `GestionDTO.active` | Direct field on DTO |
| `pagos.py` | `Payment.active` | Direct field on entity |
| `facturacion.py` | `Invoice.active` | Direct field on entity |
| `grupos.py` | `GroupClaim.active` | Direct field on entity |
| `periodos.py` | `Invoice.active` | Direct field on entity |

**Scenario: Inactive rows visually distinct in all tables**

- GIVEN a table renders an entity where `active=False`
- THEN the row SHALL have `opacity-50` and muted text
- AND controls within the row SHALL remain functional

**Scenario: Visual difference clear across tables**

- GIVEN a table with mixed active and inactive rows
- THEN the visual difference SHALL be noticeable at a glance
- AND consistent across all affected pages

---

## EXISTING Behavior (unchanged)

- The `/gestiones` page still fetches all claims, joins type-specific data, and supports sort/paginate/filter as specified in `claim-listing`.
- The `/documentos` page still offers List/Categorías toggle, document selection, related-entities table, and download endpoint as specified in `document-gallery`.
- The claim-registration form at `/gestiones/nueva` still dispatches by type (SOS vs Grouped) and creates claims atomically.
- The claim-detail page at `/gestiones/{id}` still shows claim header, type-specific section, payments table, and document section.
- Delete, active/inactive filter, row-click navigation, and all existing CRUD operations remain unchanged.
- The home page dashboard (`/`) and its `ui.table` component remain unchanged.
- Reportes page remains unchanged.

---

## MODIFIED Requirements

None — all requirements above are ADDED. No existing requirements are changed or removed.
