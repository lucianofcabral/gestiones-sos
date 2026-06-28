# Delta for Claim-Listing (Gestiones Table Refactoring)

## MODIFIED Requirements

### Requirement: Navigate to Claim Detail

Each row in the `/gestiones` table MAY be clickable for row selection/highlighting; however, navigation to `/gestiones/{claim_id}` MUST NOT occur on row click. Instead, all navigation and actions MUST be triggered exclusively through action icons in the Acciones column. The entire row appearance remains as a normal clickable area, but has no side effects.

(Previously: "Each row in the `/gestiones` table SHALL be clickable. When clicked, the system SHALL navigate to `/gestiones/{claim_id}` to display the full claim detail page. The click target SHALL be the entire row — not just a specific button or cell.")

#### Scenario: Row click does not navigate

- GIVEN the agent is viewing the gestiones list at `/gestiones`
- WHEN the agent clicks anywhere on a table row (but not on action icons)
- THEN no navigation occurs
- AND no visual selection/highlight is applied to the row
- AND the row appears as normal clickable area but produces no effect

#### Scenario: Edit action icon navigates to detail

- GIVEN the agent is viewing `/gestiones`
- WHEN the agent clicks the edit icon (pencil) in the Acciones column
- THEN the system SHALL navigate to `/gestiones/{claim_id}` for that row's claim

#### Scenario: Navigation preserves back context

- GIVEN the agent navigates from `/gestiones` to `/gestiones/{claim_id}` via action icon
- WHEN the agent clicks the back link on the detail page
- THEN the system SHALL return to `/gestiones` with the same active/inactive filter state

### Requirement: Listar Gestiones with ui.table

The `/gestiones` page MUST convert from manual `ui.row()` layout to a native `ui.table` component. The table SHALL display all Claims, SosClaims, and GroupedClaims joined in-memory, with columns: Tipo, Gestión, Asegurado, Póliza, Patente, Monto, Fecha, Resuelto, Cant. Pagos, Acciones.

All column widths, alignments, and sorting behavior MUST match the current manual implementation exactly.

(Previously: Listed with manual ui.row() layout; column widths and spacing controlled via inline CSS classes)

#### Scenario: Table renders with ui.table component

- GIVEN the database contains active claims with associated SosClaims and Grouped claims
- WHEN the user navigates to `/gestiones`
- THEN a native `ui.table` renders all claims
- AND table rows, headers, and cells use semantic HTML structure (`<table>`, `<thead>`, `<tbody>`, `<tr>`, `<td>`)

#### Scenario: Column widths and alignments preserved

- GIVEN the table renders with all 10 columns
- WHEN inspected in browser
- THEN column widths match current page (Tipo w-20, Asegurado flex, Monto right-aligned, etc.)
- AND text alignment preserved (Monto right-aligned, all others left)
- AND no text overflow visible; long text truncated with ellipsis

#### Scenario: Sortable columns toggle direction

- GIVEN the table is displayed with sortable columns
- WHEN user clicks on any column header (e.g., "Monto")
- THEN table re-sorts rows by that column (ascending first click, descending on next click)
- AND sort direction indicator (▲ or ▼) appears next to header
- AND all filter selections preserved while sorting

#### Scenario: 12-item pagination displays correctly

- GIVEN 100+ claims in the repository
- WHEN table renders
- THEN pagination UI shows current page, page size (12 items per page)
- AND "< Anterior" and "Siguiente >" buttons functional
- AND pagination behavior identical to current manual page

### Requirement: Inactive Row Styling with ui.table

Rows where `GestionDTO.active == False` MUST display with `class='table-inactive-row'`, which applies left border 2px orange-400 and opacity 0.55. This styling is identical across all refactored tables.

(Previously: Applied reduced opacity and muted text color via `opacity-50` class)

#### Scenario: Inactive claim row displays with orange border

- GIVEN a claim with active=False
- WHEN rendered in gestiones table
- THEN row displays: `class='table-inactive-row'` which applies:
  - Left border: 2px solid rgb(249, 115, 22) [orange-400]
  - Opacity: 0.55
  - Text remains readable

#### Scenario: Inactive rows remain fully interactive

- GIVEN an inactive row with class='table-inactive-row'
- WHEN user clicks action icons or the row itself
- THEN action handlers execute normally
- AND all actions (edit, delete, etc.) work as expected

### Requirement: Inline Action Icons

Each row MUST display action icons in the Acciones column. Actions MUST NOT be grouped in a dropdown menu; instead, all applicable icons for the row MUST be individually visible. All row interactions — navigation, dialogs, CRUD operations — MUST be triggered exclusively through action icons, never through row click.

(Previously: Actions grouped in dropdown menu with `ui.button` + `ui.menu`)

#### Scenario: Action icons render for every row

- GIVEN the user is viewing `/gestiones`
- THEN each row SHALL show action icons in the Acciones column at the right end:
  - Edit (pencil icon): always visible
  - Grupo (group icon): visible only if claim.group_id is set
  - Pagos (payment icon): visible if not solved
  - NC (credit note icon): visible if claim has NC
  - Delete (trash icon): always visible
- AND each icon has a tooltip showing action name

#### Scenario: Edit icon navigates to claim detail

- GIVEN the user clicks the edit (pencil) icon in Acciones
- THEN the system SHALL navigate to `/gestiones/{claim_id}`

#### Scenario: Grupo icon opens group edit dialog

- GIVEN a row has `group_id` set
- WHEN the user clicks the group icon
- THEN the system SHALL open `edit_group_dialog` from `grupos.py`
- AND on save, table refreshes

#### Scenario: Pagos icon opens payment creation form

- GIVEN the claim is not solved
- WHEN the user clicks the Pagos icon
- THEN the system SHALL open `pago_dialog` with claim_id pre-filled
- AND on save, table refreshes

#### Scenario: NC icon opens NC management dialog

- GIVEN the user clicks the NC icon
- THEN behavior depends on existing NC state:
  - If NC exists: open NC edit/delete dialog with current values
  - If no NC exists: open NC creation dialog with payer/payee/via pre-filled and locked

#### Scenario: Delete icon opens confirmation and soft-deletes

- GIVEN the user clicks the delete (trash) icon
- WHEN the user confirms in the dialog
- THEN `EliminarGestionSOS` or `EliminarGroupedClaim` executes (per claim type)
- AND claim becomes inactive
- AND table refreshes

---

## ADDED Requirements

### Requirement: Badge Styling for Status Columns

Badge components used in Monto, Resuelto, and other status columns MUST use the Badge helper component from ui-table-components spec. Color mapping: green (active/resolved), red (rejected), yellow (pending).

#### Scenario: Resuelto column shows status badge

- GIVEN a claim with `solved=True`
- WHEN table renders Resuelto column
- THEN displays Badge(text="Resuelto", color='green')
- AND styling: `text-xs font-bold px-2 py-0.5 rounded-full bg-green-600 text-white`

#### Scenario: Badge colors consistent across table

- GIVEN claims with varying solved status
- WHEN table renders
- THEN all status badges use identical Badge helper styling
- AND colors match current page badge styling exactly

---

## REMOVED Requirements

### Requirement: Row Click for Selection/Highlighting

The previous requirement for row-level visual selection state (used to highlight the clicked row) is removed. Rows no longer highlight on click. Focus is entirely on action icons.

(Reason: Shift to action-button-only interaction pattern; row click disabled per corrected specifications)
