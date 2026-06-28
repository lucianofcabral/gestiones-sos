# Delta for Periods CRUD (Periodos Table Refactoring)

## ADDED Requirements

### Requirement: Period Card Layout with Nested Tables

The periodos page MUST display Period entities as expandable cards. Each card header shows period summary; when expanded, card MUST contain two nested tables: one for Invoices, one for NcPayments (credit notes). Both nested tables MUST use `ui.table` component with identical styling and interaction patterns to main pages.

#### Scenario: Period card displays summary header

- GIVEN multiple periods exist
- WHEN periodos page loads
- THEN each period displays as an expandable card
- AND header shows: Period year/month, count of invoices, count of NCs, total invoice amount, total NC amount

#### Scenario: Expand card reveals nested tables

- GIVEN a period card
- WHEN user clicks expand button
- THEN card expands to reveal two tables:
  - Table 1: Invoices for this period (Número, Fecha, Monto, Descripción, Activo, Acciones)
  - Table 2: NcPayments for this period (Monto, Pagador, Medio, Beneficiario, Fecha, Activo, Acciones)

#### Scenario: Invoice table renders with ui.table

- GIVEN period expanded
- WHEN invoice table rendered
- THEN uses native `ui.table` component
- AND columns: Número, Fecha, Monto, Descripción, Activo, Acciones
- AND uses semantic HTML structure
- AND sorting and filtering functional

#### Scenario: NC table renders with ui.table

- GIVEN period expanded
- WHEN NC table rendered
- THEN uses native `ui.table` component
- AND displays NcPayments with related entity data pre-resolved
- AND sorting and filtering functional within card context

### Requirement: Inactive Invoice Styling in Nested Table

Invoices where `active == False` in nested period tables MUST display with `class='table-inactive-row'`, applying left border 2px orange-400 and opacity 0.55.

#### Scenario: Inactive invoice highlighted in period card

- GIVEN period expanded with inactive invoice in nested table
- WHEN invoice row rendered
- THEN row displays: `class='table-inactive-row'`
- AND left border 2px orange-400, opacity 0.55
- AND styling identical to main facturación table inactive rows

### Requirement: Inactive NC Styling in Nested Table

NcPayments where `active == False` in nested period tables MUST display with `class='table-inactive-row'`, applying left border 2px orange-400 and opacity 0.55.

#### Scenario: Inactive NC highlighted in period card

- GIVEN period expanded with inactive NC in nested table
- WHEN NC row rendered
- THEN row displays: `class='table-inactive-row'`
- AND styling identical to inactive invoices and other entities

### Requirement: Nested Table Pagination

Both nested tables (invoices and NCs) within a period card MUST support pagination with 12 items per page. Pagination UI shows current page and navigation buttons. Sort and filter within card context do not affect parent period list.

#### Scenario: Invoice pagination works within card

- GIVEN period contains 50+ invoices
- WHEN period card expanded and invoice table renders
- THEN pagination UI shows 12 items per page
- AND "< Anterior" and "Siguiente >" buttons work within nested context
- AND pagination independent of main periods list pagination

#### Scenario: NC pagination works within card

- GIVEN period contains 50+ NcPayments
- WHEN period card expanded
- THEN NC table pagination shows 12 items per page
- AND navigation buttons work independently of invoice pagination

---

## ADDED Requirements for Grupos Table

### Requirement: Grupos Table with ui.table Component

The grupos listing within periodos view (or separate grupos page if exists) MUST display a native `ui.table` component. Table SHALL display 6 columns: Nombre, Creado, Descripción, Gestiones (count), Monto Total (aggregated sum), Acciones.

#### Scenario: Grupos table renders with aggregated stats

- GIVEN multiple grupos exist with associated claims and payments
- WHEN grupos table renders
- THEN columns displayed: Nombre, Creado, Descripción, Gestiones, Monto Total, Acciones
- AND Gestiones column shows count of claims in group
- AND Monto Total shows sum of all claim amounts in group
- AND stats aggregated before render (no N+1 queries)

#### Scenario: Monto Total column right-aligned

- GIVEN grupos with varying total amounts
- WHEN table renders
- THEN Monto Total column displays with `text-right` alignment
- AND decimal points vertically align

#### Scenario: Inactive grupos highlighted

- GIVEN grupo has active=False
- WHEN rendered in table
- THEN row displays: `class='table-inactive-row'`
- AND left border 2px orange-400, opacity 0.55
- AND styling identical to other entities

### Requirement: Grupos Sorting and Filtering

Grupos table MUST support sorting on all columns and filtering by: text search (name/description), active_only checkbox. Sort direction toggles on same column.

#### Scenario: Sort by Nombre

- GIVEN multiple grupos with varying names
- WHEN user clicks Nombre column header
- THEN table sorts alphabetically; clicking again reverses
- AND sort direction indicator shown in header

#### Scenario: Sort by Monto Total

- GIVEN grupos with varying total amounts
- WHEN user clicks Monto Total column header
- THEN table sorts by amount; clicking again reverses
- AND decimal points vertically align

#### Scenario: Filter by name text

- GIVEN grupos with various names
- WHEN user enters search text and applies
- THEN table shows only grupos matching name or description
- AND sorting still works within filtered set

#### Scenario: Active only filter

- GIVEN active and inactive grupos exist
- WHEN user enables "Solo activos" checkbox
- THEN table shows only active=True grupos
- AND can be disabled to show all

### Requirement: Grupos Action Icons

Each grupo row MUST display action icons in the Acciones column: Edit (pencil), Inactivate (disable icon), and Delete (trash).

#### Scenario: Edit icon opens grupo edit dialog

- GIVEN user clicks edit icon on grupo row
- WHEN dialog opens
- THEN grupo data pre-fills
- AND save updates grupo and refreshes table

#### Scenario: Inactivate icon toggles active state

- GIVEN grupo with active=True
- WHEN user clicks inactivate icon
- THEN grupo marked inactive and table refreshes
- AND row styled with `class='table-inactive-row'`

#### Scenario: Delete icon opens confirmation

- GIVEN user clicks delete icon
- WHEN user confirms
- THEN grupo deleted (if no claims linked)
- AND table refreshes
- AND error shown if deletion blocked due to linked claims

---

## Implementation Notes

- Both nested invoice and NC tables use `ui.table` with same styling as standalone pages
- Inactive row styling via `class='table-inactive-row'` defined in global stylesheet
- All entity lookups and aggregations computed before render to avoid N+1
- Grupos stats (Gestiones count, Monto Total) pre-calculated before table render
- Pagination independent between nested tables and parent periods list
- Sort and filter behavior identical to current page implementation
