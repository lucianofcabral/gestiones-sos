# Delta for Group Claim (Grupos Table Refactoring)

## ADDED Requirements

### Requirement: Grouped Claims Table within Grupo Detail

When a grupo is opened for detail/edit, a nested `ui.table` component MUST display all claims belonging to that grupo. Table SHALL display columns: Tipo, Gestión, Asegurado, Póliza, Patente, Monto, Fecha, Resuelto, Cant. Pagos, Acciones.

All column widths, alignments, and interactions MUST match the main gestiones `/gestiones` table exactly.

#### Scenario: Grupo detail page displays grouped claims table

- GIVEN a grupo is opened for detail/edit
- WHEN page renders
- THEN `ui.table` displays all claims linked to this grupo
- AND columns: Tipo, Gestión, Asegurado, Póliza, Patente, Monto, Fecha, Resuelto, Cant. Pagos, Acciones
- AND uses semantic HTML structure (`<table>`, `<thead>`, `<tbody>`, `<tr>`, `<td>`)

#### Scenario: Column widths and alignments preserved from main gestiones table

- GIVEN grouped claims table renders
- WHEN inspected in browser
- THEN column widths match main `/gestiones` table (Tipo w-20, Asegurado flex, Monto right-aligned, etc.)
- AND text alignment identical (Monto right-aligned, others left)
- AND no text overflow visible; long text truncated with ellipsis

#### Scenario: Inactive grouped claims highlighted

- GIVEN a grouped claim with active=False
- WHEN rendered in grupo detail table
- THEN row displays: `class='table-inactive-row'`
- AND left border 2px orange-400, opacity 0.55
- AND styling identical to main gestiones table

### Requirement: Grouped Claims Sorting and Filtering

The grouped claims table within grupo detail MUST support sorting on all columns and filtering by: text search, active_only checkbox. Sorting and filtering MUST work independently of the main `/gestiones` page.

#### Scenario: Sort by column in grupo detail table

- GIVEN grouped claims table
- WHEN user clicks any column header (e.g., "Monto")
- THEN table re-sorts by that column (ascending first, descending next)
- AND sort direction indicator shown in header
- AND sort state independent of main `/gestiones` page

#### Scenario: Filter within grupo detail

- GIVEN grouped claims table
- WHEN user applies filter (text search or active_only)
- THEN table shows only matching claims within this grupo
- AND other filter states (on main page) unaffected
- AND pagination resets to page 1 within grupo context

#### Scenario: 12-item pagination within grupo detail

- GIVEN grupo contains 50+ claims
- WHEN grouped claims table renders
- THEN pagination UI shows 12 items per page
- AND "< Anterior" and "Siguiente >" buttons functional
- AND pagination independent of main `/gestiones` list pagination

### Requirement: Action Icons on Grouped Claims

Each row in the grouped claims table MUST display action icons in the Acciones column: Edit (pencil), Pagos (payment), NC (credit note), Unlink (unlink from group), and Delete (trash).

Visibility and behavior:

- **Edit**: always visible, navigates to `/gestiones/{claim_id}`
- **Pagos**: always visible if not solved, opens payment creation dialog
- **NC**: visible if claim has NC or can create NC, opens NC management dialog
- **Unlink**: always visible, calls `ActualizarGrupoDeGestion` with `new_group_id=None` and refreshes table
- **Delete**: always visible, opens confirmation and soft-deletes claim

#### Scenario: Edit icon navigates to claim detail

- GIVEN user clicks edit icon on grouped claim row
- WHEN click executes
- THEN system navigates to `/gestiones/{claim_id}`

#### Scenario: Pagos icon opens payment creation

- GIVEN user clicks Pagos icon on unsolved grouped claim
- WHEN click executes
- THEN payment dialog opens with this grupo's claim_id pre-filled
- AND on save, grouped claims table refreshes

#### Scenario: Unlink icon removes claim from grupo

- GIVEN user clicks unlink icon
- WHEN user confirms
- THEN `ActualizarGrupoDeGestion(claim_id, new_group_id=None)` executes
- AND claim removed from grupo
- AND grouped claims table refreshes
- AND main `/gestiones` table updated to show ungrouped claim

#### Scenario: Delete icon soft-deletes grouped claim

- GIVEN user clicks delete icon on grouped claim
- WHEN user confirms
- THEN claim soft-deleted (inactive=True)
- AND claim remains in table but styled with `class='table-inactive-row'`
- AND grouped claims table refreshes

### Requirement: Inactive Grouped Claims Styling

Rows where the claim's `active == False` MUST display with `class='table-inactive-row'`, applying left border 2px orange-400 and opacity 0.55. Styling identical to main `/gestiones` table.

#### Scenario: Inactive grouped claim highlighted

- GIVEN a grouped claim with active=False
- WHEN rendered in grupo detail table
- THEN row displays: `class='table-inactive-row'`
- AND left border 2px orange-400, opacity 0.55
- AND styling identical to main gestiones table inactive rows

#### Scenario: Inactive grouped claims remain interactive

- GIVEN an inactive grouped claim row
- WHEN user clicks action icons
- THEN handlers execute normally
- AND all actions work as expected

---

## Implementation Notes

- Grouped claims table uses identical styling and column definitions as main `/gestiones` table
- All sorting and filtering state independent of main page
- Unlink action calls shared use case `ActualizarGrupoDeGestion` already used on main `/gestiones` page
- Inactive row styling via `class='table-inactive-row'` defined in global stylesheet
- Pagination independent between grupo detail table and main list
- Edit action navigates away from grupo detail; unlink keeps user on same page with refreshed table
