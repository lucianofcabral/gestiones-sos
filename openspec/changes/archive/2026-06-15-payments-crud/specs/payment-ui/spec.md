# Payment UI Specification

## Purpose

Dedicated `/pagos` page with a refreshable table, modal CRUD dialogs, agent-name resolution, filters, and NC payment sub-section. The domain layer (use cases, services, ports) is already complete — this spec covers exclusively the UI surface.

## Requirements

### Requirement: Payment List View

The `/pagos` page MUST render a table with columns: payer name, payee name, payment method, amount, date, active status. Agent names SHALL be resolved from UUIDs via `AgentRepoPort.get_by_id()` at render time.

#### Scenario: Table with agent names

- GIVEN payments exist in the store
- WHEN the page loads
- THEN the table displays each row with payer/payee names (not UUIDs) and payment method names (not IDs)

#### Scenario: Empty state

- GIVEN no payments exist
- WHEN the page loads
- THEN the system displays an empty-state message ("No hay pagos registrados")

### Requirement: Create Payment Dialog

The system MUST open a modal dialog for payment creation. Form fields: claim_id (text input), payer (agent picker), payee (agent picker), payment_via (dropdown), amount (number), period_id (conditional — show when payment_via is NC).

#### Scenario: Create transferencia payment

- GIVEN the create dialog is open with valid claim_id, payer, payee, payment_via (not NC), and amount
- WHEN the user submits
- THEN the system calls `RegistrarPago.execute()` and the new row appears in the table

#### Scenario: Create NC payment with period

- GIVEN the create dialog is open and payment_via is NC
- WHEN the user selects payment_via="Nota de Crédito"
- THEN the period_id field SHALL appear and MUST be required
- WHEN the user submits with all valid fields
- THEN the system creates both Payment and CreditNote, and the row appears

#### Scenario: Form validation

- GIVEN the create dialog is open
- WHEN the user submits with empty required fields (claim_id, payer, payee, payment_via, amount)
- THEN the system SHOWs a warning notification with the missing field list and does NOT submit

### Requirement: Edit Payment Dialog

The system MUST open a modal dialog pre-filled with current payment values. When a linked NC exists, `PaymentUpdateRules` MUST restrict fields — only amount is editable.

#### Scenario: Edit without NC — full edit

- GIVEN a payment with no linked CreditNote
- WHEN the edit dialog opens
- THEN payer, payee, payment_via, and amount are all editable
- WHEN the user changes amount and saves
- THEN the system calls `ActualizarPago.execute()` and updates the row

#### Scenario: Edit with NC — amount only

- GIVEN a payment with a linked CreditNote
- WHEN the edit dialog opens
- THEN payer, payee, and payment_via are DISABLED with a tooltip "Only amount can be modified when a credit note exists"
- AND only amount is editable
- WHEN the user saves a new amount
- THEN the system updates and refreshes the table

#### Scenario: Edit non-existent payment

- GIVEN the edit dialog is open for a payment that no longer exists
- WHEN the user saves
- THEN the system shows a negative notification and closes the dialog without changes

### Requirement: Inactivate / Activate Payment

The system MUST provide inline buttons to toggle active status, with confirmation showing the eligibility reason from domain services.

#### Scenario: Inactivate eligible payment

- GIVEN a payment with `active=True` and no linked NC
- WHEN the user clicks inactivate
- THEN a confirmation dialog SHOWs "¿Inactivar pago?" with reason "No credit note associated"
- WHEN the user confirms
- THEN the system calls `InactivarPago.execute()` and refreshes the table

#### Scenario: Inactivate with NC — blocked

- GIVEN a payment with `active=True` and a linked NC tied to a closed period
- WHEN the user clicks inactivate
- THEN the system SHOWs a notification "Cannot inactivate: credit note linked to a closed period"
- AND does NOT open the confirmation dialog

#### Scenario: Activate payment

- GIVEN a payment with `active=False` whose claim is active
- WHEN the user clicks activate
- THEN the system calls `ActivarPago.execute()` and refreshes the table

### Requirement: Agent Name Resolution

The system MUST resolve `payer_id` and `payee_id` UUIDs to agent names for display in the table and dialogs.

#### Scenario: Resolve agent names

- GIVEN a payment with `payer_id` and `payee_id`
- WHEN the table renders
- THEN each row SHOWs the resolved `Agent.name` instead of the UUID

#### Scenario: Agent missing

- GIVEN a payment references an agent UUID not present in the store
- WHEN the table renders
- THEN the system SHOWs "—" for the missing agent name instead of crashing

### Requirement: Filters

The page MUST provide a filter bar with: claim_id (exact match), date range (start/end), amount range (min/max), active/inactive toggle (default: all).

#### Scenario: Filter by claim ID

- GIVEN payments for multiple claims exist
- WHEN the user enters a claim_id and applies the filter
- THEN the table SHOWs only payments matching that claim_id

#### Scenario: Filter by date range

- GIVEN payments with various `created_date` values
- WHEN the user enters a start and end date
- THEN the table SHOWs only payments within that range

#### Scenario: Filter by active status

- GIVEN both active and inactive payments exist
- WHEN the user toggles the active-only filter
- THEN the table SHOWs only active payments

### Requirement: NC Payment Sub-section

Each payment row MUST have an expandable section showing linked CreditNotes. The section SHALL allow: create NC, mark delivered, inactivate NC.

#### Scenario: View NCs for a payment

- GIVEN a payment with linked CreditNotes
- WHEN the user expands the row
- THEN the section SHOWs each NC with columns: period, delivered status, active status, created date

#### Scenario: Create NC from payment

- GIVEN a payment expand section is open
- WHEN the user clicks "Agregar Nota de Crédito" and selects a period
- THEN the system calls `RegistrarNotaCredito.execute()` and the new NC appears in the section

#### Scenario: Mark NC delivered

- GIVEN an NC with `delivered=False`
- WHEN the user clicks the mark-delivered button in the NC row
- THEN the system calls `MarcarNcEntregada.execute()` and updates the NC row status

#### Scenario: Inactivate NC

- GIVEN an NC with `active=True`
- WHEN the user clicks inactivate on the NC row
- THEN the system calls `InactivarNc.execute()` and the NC row updates
