# UI Table Components — New Specification

## Purpose

Define reusable helper components and styling conventions for converting 6 pages from manual `ui.row()` tables to native `ui.table()` components. Ensures visual consistency and reduces duplication across gestiones, pagos, facturacion, periodos, grupos, and documentos pages.

## Requirements

### Requirement: Badge Helper Component

The system SHALL provide a `Badge(text: str, color: str)` helper that renders status badges with consistent styling across all tables.

**Supported colors**: `green` (active), `red` (rejected), `yellow` (pending), `blue` (informational), `purple` (category-specific)

#### Scenario: Render active badge

- GIVEN a badge with text="Activo" and color='green'
- WHEN rendered in a table cell
- THEN displays: `text-xs font-bold px-2 py-0.5 rounded-full bg-green-600 text-white`

#### Scenario: Render pending badge

- GIVEN a badge with text="Pendiente" and color='yellow'
- WHEN rendered in a table cell
- THEN displays: `text-xs font-bold px-2 py-0.5 rounded-full bg-yellow-500 text-white`

#### Scenario: Render category badge (invoices)

- GIVEN a badge with text="Factura" and color='blue'
- WHEN rendered in a table cell
- THEN displays: `text-xs font-bold px-2 py-0.5 rounded-full bg-blue-600 text-white`

### Requirement: ActionButton Helper Component

The system SHALL provide an `ActionButton(icon: str, label: str, on_click: Callable)` helper that renders action buttons with consistent styling and tooltips.

**Supported icons**: `edit`, `delete`, `groups`, `receipt_long`, `credit_card`, `add`

#### Scenario: Render edit button with tooltip

- GIVEN an action button with icon='edit', label='Editar'
- WHEN rendered in a table action cell
- THEN displays: flat, dense, round, size=sm properties
- AND shows tooltip with label on hover

#### Scenario: Render delete button in confirmation mode

- GIVEN an action button with icon='delete', label='Eliminar'
- WHEN user hovers
- THEN tooltip shows "Eliminar"
- AND click opens confirmation dialog

### Requirement: Inactive Row Styling

The system SHALL apply consistent styling to rows where the entity's `active` field is `False`. All inactive rows across all tables MUST use identical CSS classes.

#### Scenario: Inactive claim row displays with orange border

- GIVEN a claim with active=False
- WHEN rendered in gestiones table
- THEN row displays: `class='table-inactive-row'` which applies:
  - Left border: 2px solid rgb(249, 115, 22) [orange-400]
  - Opacity: 0.55
  - Text remains readable

#### Scenario: Inactive payment row displays with same styling

- GIVEN a payment with active=False
- WHEN rendered in pagos table
- THEN row displays: `class='table-inactive-row'`
- AND visual appearance identical to inactive gestiones rows

#### Scenario: Inactive row remains interactive

- GIVEN an inactive row with class='table-inactive-row'
- WHEN user clicks the row or action buttons
- THEN click handlers execute normally
- AND row selection/navigation works

### Requirement: Table Column Alignment Conventions

The system SHALL standardize column alignment across all refactored tables. Numerical columns (amounts, counts) right-align; text columns left-align.

#### Scenario: Monto column right-aligns

- GIVEN a table with a Monto (amount) column
- WHEN rendered
- THEN numbers display with `text-right` alignment
- AND decimal points vertically align

#### Scenario: Text columns left-align

- GIVEN a table with text columns (Gestión, Cliente, Descripción)
- WHEN rendered
- THEN all text displays with `text-left` alignment

### Requirement: Semantic Table HTML Structure

The system SHALL render all refactored tables with proper semantic HTML (`<table>`, `<thead>`, `<tbody>`, `<tr>`, `<td>`) and ARIA attributes for accessibility.

#### Scenario: Table has semantic structure

- GIVEN a ui.table component rendered
- WHEN inspected in browser DevTools
- THEN HTML contains proper `<table>`, `<thead>`, `<tbody>` tags
- AND Quasar q-table provides ARIA attributes for screen reader navigation

#### Scenario: Screen reader announces column headers

- GIVEN a table with column headers
- WHEN screen reader navigates the table
- THEN headers are announced before each column data

---

## Implementation Notes

- Badge colors map to Tailwind palette; verify hex values match current page styling
- ActionButton tooltips use `ui.tooltip()` pattern per NiceGUI conventions
- `table-inactive-row` CSS class defined once in global stylesheet, reused across all 6 pages
- No N+1 queries during table render; all related data pre-loaded before component instantiation
