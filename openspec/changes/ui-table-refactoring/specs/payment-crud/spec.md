# Delta for Payment CRUD (Pagos Table Refactoring)

## ADDED Requirements

### Requirement: List Payments with ui.table Component

The payments listing page (pagos.py) MUST render a native `ui.table` component displaying all Payments with pre-resolved related entities (Agent names, PaymentVia names, Claim references, Group references, ClaimKind, NcPayment status). Table SHALL display 14 columns: Monto, Pagador, Medio, Beneficiario, Cliente, Tipo, Grupo, Dominio, Póliza, Gestión, Fecha, NC, Activo, Acciones.

All data lookups MUST be computed before table render to avoid N+1 queries. Table SHALL support multi-filter, sorting on all 14 columns, and custom pagination (12 items per page).

#### Scenario: Table renders with all 14 columns

- GIVEN payments list with related entities pre-resolved
- WHEN ui.table renders on pagos page
- THEN table displays columns: Monto, Pagador, Medio, Beneficiario, Cliente, Tipo, Grupo, Dominio, Póliza, Gestión, Fecha, NC, Activo, Acciones
- AND all data pre-resolved before render (no N+1 lookups)
- AND column alignments correct (Monto right-aligned, others left)

#### Scenario: Monto column displays amount right-aligned

- GIVEN payments with varying amounts
- WHEN rendered in table
- THEN Monto column displays with `text-right` alignment
- AND decimal points vertically align
- AND values match Payment.amount exactly

#### Scenario: Agent columns resolve to display names

- GIVEN payments with payer_id and payee_id references
- WHEN table renders
- THEN Pagador and Beneficiario columns show Agent display names
- AND names resolved once before render, not per row

#### Scenario: PaymentVia column resolved to display name

- GIVEN payments with payment_via_id
- WHEN table renders
- THEN Medio column shows PaymentVia display name
- AND lookup done once before render

#### Scenario: Claim and Group data pre-loaded

- GIVEN payments with claim_id and group_id references
- WHEN table renders
- THEN claim detail (Póliza, Gestión) and group name pre-loaded
- AND available for render without additional queries

#### Scenario: 12-item pagination displays correctly

- GIVEN 100+ payments
- WHEN table renders
- THEN pagination UI shows current page, page size (12 items)
- AND "< Anterior" and "Siguiente >" buttons functional
- AND pagination behavior identical to current page

### Requirement: Multi-Filter Support for Payments

The pagos table MUST support filtering by: `claim_id`, `date_from`, `date_to`, `amount_min`, `amount_max`, `active_only` checkbox, and text search. Filters MUST work with ui.table sorting and pagination. Filter application MUST reset pagination to page 1.

#### Scenario: Filter by claim_id

- GIVEN multiple payments across different claims
- WHEN user selects a claim_id filter and clicks "Aplicar Filtros"
- THEN table shows only payments for that claim
- AND pagination resets to page 1

#### Scenario: Filter by date range

- GIVEN payments with varying created_date values
- WHEN user enters date_from and date_to and applies filters
- THEN table shows only payments within range (inclusive)
- AND sorting still works within filtered set

#### Scenario: Filter by amount range

- GIVEN payments with amounts from 100 to 10000
- WHEN user enters amount_min=500 and amount_max=5000 and applies
- THEN table shows only payments within range
- AND can combine with other filters

#### Scenario: Active only filter excludes inactive

- GIVEN active and inactive payments exist
- WHEN user enables "Solo activos" checkbox
- THEN table shows only active=True payments
- AND can be disabled to show all payments

#### Scenario: Text search filters across multiple columns

- GIVEN payments with agent names, claim references, etc.
- WHEN user enters search text and applies
- THEN table searches and matches across Pagador, Beneficiario, Cliente, Gestión columns
- AND filter combines with other filters using AND logic

### Requirement: Inactive Payment Row Styling

Rows where `Payment.active == False` MUST display with `class='table-inactive-row'`, applying left border 2px orange-400 and opacity 0.55. Styling identical across all refactored tables.

#### Scenario: Inactive payment highlighted with orange border

- GIVEN a payment with active=False
- WHEN rendered in pagos table
- THEN row displays: `class='table-inactive-row'`
- AND left border 2px orange-400, opacity 0.55
- AND styling identical to inactive gestiones rows

#### Scenario: Inactive rows remain interactive

- GIVEN an inactive row
- WHEN user clicks action icons
- THEN handlers execute normally
- AND row can be reactivated via action button

### Requirement: NC Status Badge Column

The NC column MUST display Badge components showing NC payment status: "Entregado" (green) if NC.delivered=True, "Pendiente" (yellow) if NC.delivered=False, or empty if no NC linked.

#### Scenario: NC Entregado badge renders

- GIVEN a payment has linked NC with delivered=True
- WHEN NC column renders
- THEN displays Badge(text="Entregado", color='green')
- AND styling: `text-xs font-bold px-2 py-0.5 rounded-full bg-green-600 text-white`

#### Scenario: NC Pendiente badge renders

- GIVEN a payment has linked NC with delivered=False
- WHEN NC column renders
- THEN displays Badge(text="Pendiente", color='yellow')
- AND styling: `text-xs font-bold px-2 py-0.5 rounded-full bg-yellow-500 text-white`

#### Scenario: No NC shows empty cell

- GIVEN a payment has no linked NC
- WHEN NC column renders
- THEN cell is empty (no badge)

### Requirement: Activo Status Column

The Activo column MUST display Badge component showing "Activo" (green) if active=True, or "Inactivo" (red) if active=False.

#### Scenario: Active payment shows Activo badge

- GIVEN payment with active=True
- WHEN Activo column renders
- THEN displays Badge(text="Activo", color='green')

#### Scenario: Inactive payment shows Inactivo badge

- GIVEN payment with active=False
- WHEN Activo column renders
- THEN displays Badge(text="Inactivo", color='red')

### Requirement: Payment Action Icons

Each row MUST display action icons in the Acciones column: Edit (pencil), Inactivate (disable icon), and Delete (trash). Visibility and behavior:

- **Edit**: always visible, opens payment edit dialog
- **Inactivate/Activate**: toggles payment active state (inactivate if active=True, activate if active=False)
- **Delete**: always visible, opens confirmation dialog and hard-deletes payment (if no NcPayment references it)

#### Scenario: Edit icon opens payment edit dialog

- GIVEN user clicks edit icon
- WHEN dialog opens
- THEN payment data pre-fills all fields
- AND save updates payment and refreshes table

#### Scenario: Inactivate icon toggles active state

- GIVEN payment with active=True
- WHEN user clicks inactivate icon
- THEN payment.active set to False and table refreshes
- AND row now displays with `class='table-inactive-row'`

#### Scenario: Activate icon restores active state

- GIVEN payment with active=False
- WHEN user clicks activate (restore) icon
- THEN payment.active set to True and table refreshes
- AND row styling removed

#### Scenario: Delete icon opens confirmation

- GIVEN user clicks delete icon
- WHEN user confirms
- THEN payment hard-deleted (if not referenced by NcPayment)
- AND table refreshes
- AND error shown if deletion blocked due to NcPayment reference

---

## Implementation Notes

- All entity lookups (Agent, PaymentVia, Claim, Group, ClaimKind, NcPayment) MUST be resolved once before table render
- Use single aggregate queries or batch loads to avoid N+1
- Monto column MUST right-align; all other text columns left-align
- Badge helper from ui-table-components spec used for NC and Activo columns
- Sort and filter logic identical to current page
- Inactive row styling via `class='table-inactive-row'` defined in global stylesheet
