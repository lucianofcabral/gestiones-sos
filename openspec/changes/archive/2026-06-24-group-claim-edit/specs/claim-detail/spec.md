# Delta for Claim-Detail

## ADDED Requirements

### Requirement: Inline Group Editing

The detail page SHALL provide an autocomplete/select control for the group field on all claim types. Selecting a new group SHALL invoke `ActualizarGrupoDeGestion` which validates claim and target group exist, persists the change via audited UnitOfWork, and refreshes the page.

The system MUST reject changes with an error notification and no data modification if validation fails.

#### Scenario: Happy path — agent changes group

- GIVEN a claim belongs to group "A" and group "B" exists
- WHEN the agent selects "B" from the autocomplete and confirms
- THEN the claim's group SHALL change to "B"
- AND the page SHALL refresh showing the new group name
- AND the audit log SHALL record old and new group values

#### Scenario: Claim not found

- GIVEN a claim ID does not exist
- WHEN the agent attempts a group update
- THEN the system SHALL raise `ClaimNotFoundError`
- AND the page SHALL display an error notification
- AND no audit entry SHALL be created

#### Scenario: Target group not found

- GIVEN a claim exists but the selected group ID has no matching `GroupClaim`
- WHEN the agent submits the change
- THEN the system SHALL reject with an error notification
- AND the claim's group SHALL remain unchanged

#### Scenario: Autocomplete filters by group name

- GIVEN multiple groups exist with distinct names
- WHEN the agent types a partial group name
- THEN the autocomplete SHALL display only matching groups

### Requirement: Fix Latent Update Bug

The `SqlAlchemyClaimRepository.update()` MUST persist `group_id` alongside existing columns so that the inline group editing takes effect in the database.

#### Scenario: update() writes group_id

- GIVEN a claim with group_id="A"
- WHEN `update()` is called with group_id="B"
- THEN the database row SHALL reflect group_id="B"
- AND other columns SHALL remain unchanged

## MODIFIED Requirements

### Requirement: Detail Page UI Sections

The page at `/gestiones/{id}` SHALL render sections based on claim type:

**Section 1 — Claim Header (all types):** Displays claim type badge, claimer_name (asegurado), policy_number (póliza), plate (patente), claimed_amount (monto), **editable group field (autocomplete/select with current group pre-selected)**, and claim kind name. Online gestion/reference display: SOS claims show `gestion`; Grouped claims show `external_reference` from the linked batch.
(Previously: group name was read-only text)

**Section 2a — SOS Records Table (SOS type only):** Displays all SosClaim records with columns: gestion number, category, reason, status, load_user, response_user, itr. If no records exist, the table body shows an empty-state label.

**Section 2b — Grouped Data Card (Grouped type only):** Displays batch external_reference, description, notes, and creation date.

**Section 3 — Payments Table (all types):** Displays payments with columns: amount, created_date, payer_id, payee_id, payment_via_id. Agent/via names are raw UUIDs in v1.

The page SHALL include a back navigation link to `/gestiones`.

#### Scenario: Back navigation

- GIVEN the agent is viewing a claim detail page
- WHEN the agent clicks the back link
- THEN the system SHALL navigate to `/gestiones`

#### Scenario: SOS detail shows all three sections

- GIVEN a claim of type `sos` with SosClaims and payments
- WHEN the agent views `/gestiones/{claim_id}`
- THEN the header SHALL include the gestion number and SOS type badge
- AND Section 2a (SOS Records) SHALL render
- AND Section 3 (Payments) SHALL render

#### Scenario: Grouped detail shows type-specific card

- GIVEN a claim of type `grouped` with a linked batch and payments
- WHEN the agent views `/gestiones/{claim_id}`
- THEN the header SHALL include the external_reference and Grouped type badge
- AND Section 2b (Grouped Data card) SHALL render
- AND Section 2a (SOS Records) SHALL NOT render
- AND Section 3 (Payments) SHALL render

## MODIFIED Meta

### Out of Scope (v2+)

Updated to reflect group editing is now implemented:
(Previously listed "Inline editing of claim or SosClaim fields" — group editing removed)

- Document gallery display
- Agent name resolution in payments (raw IDs shown)
- Payment via name resolution (raw IDs shown)
- Inline editing of SosClaim fields
- Payment CRUD operations from the detail page
- SosClaim creation or modification
