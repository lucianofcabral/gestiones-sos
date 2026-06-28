# Delta for Billing CRUD (Facturación Table Refactoring)

## ADDED Requirements

### Requirement: Invoice Table with ui.table Component

The facturación page MUST render a native `ui.table` component displaying Invoices for the selected period. Table SHALL display 6 columns: Número, Fecha, Monto, Descripción, Activo, Acciones. All invoices (active and inactive) SHALL be displayed; inactive invoices highlighted with orange border styling.

#### Scenario: Invoice table renders for selected period

- GIVEN a period is selected
- WHEN facturación page loads
- THEN `ui.table` renders all invoices for that period
- AND columns displayed: Número, Fecha, Monto, Descripción, Activo, Acciones
- AND table uses semantic HTML structure (`<table>`, `<thead>`, `<tbody>`, `<tr>`, `<td>`)

#### Scenario: Column widths and alignments correct

- GIVEN table renders
- THEN Monto column displays with `text-right` alignment
- AND all other columns display with `text-left` alignment
- AND Descripción column expands to fill available width (flex-1)
- AND fixed-width columns (Número, Fecha, Monto, Acciones) retain compact widths

#### Scenario: All invoices displayed regardless of active state

- GIVEN period contains active and inactive invoices
- WHEN table renders
- THEN all invoices appear in table
- AND inactive invoices highlighted with orange border styling

#### Scenario: 12-item pagination displays correctly

- GIVEN 100+ invoices for a period
- WHEN table renders
- THEN pagination UI shows current page, page size (12 items)
- AND "< Anterior" and "Siguiente >" buttons functional

### Requirement: Inactive Invoice Row Styling

Rows where `Invoice.active == False` (or equivalent) MUST display with `class='table-inactive-row'`, applying left border 2px orange-400 and opacity 0.55. Styling identical across all refactored tables.

#### Scenario: Inactive invoice highlighted with orange border

- GIVEN an invoice with active=False
- WHEN rendered in facturación table
- THEN row displays: `class='table-inactive-row'`
- AND left border 2px orange-400, opacity 0.55
- AND styling identical to inactive gestiones and pagos rows

#### Scenario: Inactive rows remain interactive

- GIVEN an inactive invoice row
- WHEN user clicks action icons
- THEN handlers execute normally
- AND invoice can be reactivated or deleted

### Requirement: Activo Status Column

The Activo column MUST display Badge component showing "Activo" (green) if active=True, or "Inactivo" (red) if active=False.

#### Scenario: Active invoice shows Activo badge

- GIVEN invoice with active=True (or default active state)
- WHEN Activo column renders
- THEN displays Badge(text="Activo", color='green')
- AND styling: `text-xs font-bold px-2 py-0.5 rounded-full bg-green-600 text-white`

#### Scenario: Inactive invoice shows Inactivo badge

- GIVEN invoice with active=False
- WHEN Activo column renders
- THEN displays Badge(text="Inactivo", color='red')
- AND styling: `text-xs font-bold px-2 py-0.5 rounded-full bg-red-600 text-white`

### Requirement: Multi-Filter and Sorting

The facturación table MUST support filtering and sorting on all 6 columns. Filters include: date_from, date_to, description text search, active_only checkbox. Sort keys MUST work on all columns; sorting MUST respect filter selections.

#### Scenario: Filter by date range

- GIVEN invoices with varying emited_date
- WHEN user enters date_from and date_to and applies
- THEN table shows only invoices within range (inclusive)
- AND sorting still works within filtered set

#### Scenario: Filter by description text

- GIVEN invoices with descriptions
- WHEN user enters description text and applies
- THEN table searches description field
- AND displays matching invoices

#### Scenario: Active only filter

- GIVEN active and inactive invoices exist
- WHEN user enables "Solo activos" checkbox
- THEN table shows only active invoices
- AND can be disabled to show all invoices

#### Scenario: Sort by amount

- GIVEN invoices with varying amounts
- WHEN user clicks Monto column header
- THEN table sorts by amount ascending; clicking again reverses
- AND decimal points vertically align in sorted column

#### Scenario: Sort by date

- GIVEN invoices with varying dates
- WHEN user clicks Fecha column header
- THEN table sorts chronologically
- AND sort direction toggles on subsequent clicks

#### Scenario: Filter resets pagination

- GIVEN user on page 3 of invoices
- WHEN user applies any filter
- THEN pagination resets to page 1
- AND table shows filtered results

### Requirement: Total Billing Calculation

The facturación page MUST display total amount (sum) of all invoices currently rendered in the table (respecting filters and pagination display). Total MUST be calculated from filtered results and displayed prominently.

#### Scenario: Total calculated from visible invoices

- GIVEN table displays filtered invoices with amounts 1000, 500, 300
- WHEN pagination shows 12 invoices per page
- THEN total amount calculated and displayed from filtered set
- AND total updates when filters change

#### Scenario: Total updates on filter change

- GIVEN initial filtered total calculated
- WHEN user applies new filter reducing matching invoices
- THEN total re-calculated and updated
- AND display shows new total

### Requirement: Invoice Action Icons

Each row MUST display action icons in the Acciones column: Edit (pencil), Inactivate (disable icon), and Delete (trash). Behavior:

- **Edit**: always visible, opens invoice edit dialog (if applicable)
- **Inactivate/Activate**: toggles invoice active state
- **Delete**: always visible, opens confirmation dialog and deletes invoice (if no DocumentEntity references it)

#### Scenario: Edit icon opens invoice edit dialog

- GIVEN user clicks edit icon on invoice row
- WHEN dialog opens
- THEN invoice data pre-fills (número, fecha, monto, descripción)
- AND save updates invoice and refreshes table

#### Scenario: Inactivate icon toggles active state

- GIVEN invoice with active=True
- WHEN user clicks inactivate icon
- THEN invoice marked inactive and table refreshes
- AND row styled with `class='table-inactive-row'`

#### Scenario: Delete icon opens confirmation

- GIVEN user clicks delete icon
- WHEN user confirms
- THEN invoice deleted (if no DocumentEntity references it)
- AND table refreshes
- AND error shown if deletion blocked due to document attachment

---

## Implementation Notes

- Invoice active/inactive state determined by domain logic (check existing Invoice entity)
- Monto column MUST right-align; all other text columns left-align
- Badge helper from ui-table-components spec used for Activo column
- Sort and filter logic identical to current page
- Inactive row styling via `class='table-inactive-row'` defined in global stylesheet
- Total billing calculation from filtered results, not all period invoices
