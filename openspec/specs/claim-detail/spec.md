# Claim-Detail Specification

## Purpose

The claim-detail capability provides a detail view at `/gestiones/{id}` for agents to inspect a single claim's full information, including type-specific sections (SOS Records table or Grouped Data card), claim header with group and claim kind names, and payments. It renders dynamically based on the claim's `ClaimKind` discriminator.

## User Story

As an agent, I want to click a claim in the list and see all its details — claim header, type-specific records (SOS history or batch info), and a payments list — so I can triage, reconcile payments, and understand the full history without jumping between screens.

## Requirements

### Requirement: Obtener Gestion Por ID

The system SHALL provide a use case `ObtenerGestionPorId` that accepts a `claim_id` UUID and fetches the `Claim` by ID. Based on `Claim.claim_kind_id`, it SHALL fetch either `SosClaim` records (for SOS type) or `GroupedClaim` + `GroupClaim` batch (for Grouped type). In all cases, it SHALL fetch the `ClaimKind` name and all `Payment` records.

If the claim is not found, the use case SHALL raise `ClaimNotFoundError`.

#### Scenario: Happy path — claim with SosClaims and payments

- GIVEN a claim exists with 3 SosClaim records and 2 payments
- WHEN the agent navigates to `/gestiones/{claim_id}`
- THEN the page SHALL display the claim header (number, claimer_name, policy_number, plate, claimed_amount)
- AND the page SHALL display the group name and claim kind name
- AND the page SHALL display a table with all 3 SosClaim rows
- AND the page SHALL display a payments table with both payment entries

#### Scenario: SOS claim fetches SosClaim records

- GIVEN a claim of type `sos` exists with 3 SosClaim records and 2 payments
- WHEN the agent navigates to `/gestiones/{claim_id}`
- THEN the page SHALL display the claim header
- AND the page SHALL display the SOS Records table with 3 SosClaim rows
- AND the page SHALL display the payments table
- AND the Grouped Data card SHALL NOT render

#### Scenario: Grouped claim fetches batch info

- GIVEN a claim of type `grouped` with 1 GroupedClaim and 2 payments
- WHEN the agent navigates to `/gestiones/{claim_id}`
- THEN the page SHALL display the claim header
- AND the page SHALL display the Grouped Data card with batch info
- AND the SOS Records table SHALL NOT render
- AND the payments table SHALL render normally

#### Scenario: Claim with no SosClaim records

- GIVEN a claim exists but has no SosClaim records
- WHEN the agent navigates to `/gestiones/{claim_id}`
- THEN the SOS records section SHALL show an empty state message
- AND the claim header and payments SHALL still render normally

#### Scenario: Claim with multiple SosClaim records

- GIVEN a claim has 5 SosClaim records
- WHEN the agent navigates to `/gestiones/{claim_id}`
- THEN ALL 5 SosClaim records SHALL be visible in the SOS history table
- AND the table SHALL be scrollable

#### Scenario: Claim not found

- GIVEN a claim ID does not exist in the database
- WHEN the agent navigates to `/gestiones/{non_existent_id}`
- THEN the system SHALL NOT render a detail page
- AND the system SHALL display a `ui.notify` error message
- AND the system SHALL redirect back to `/gestiones`

#### Scenario: Database connection failure

- GIVEN the database is unreachable
- WHEN the agent navigates to `/gestiones/{claim_id}`
- THEN the system SHALL display a `ui.notify` error message
- AND the page SHALL NOT render claim data

### Requirement: Grouped Claim Batch Card

The detail page SHALL render a "Grouped Data" card for claims of type `grouped`. The card SHALL display: `GroupClaim.external_reference`, `GroupClaim.description` (or "—" if null), `GroupedClaim.notes` (or "—" if null), and batch creation date.

#### Scenario: Grouped claim shows batch info

- GIVEN a claim of type `grouped` linked to a batch with external_reference="Lote-2024-001"
- WHEN the agent navigates to `/gestiones/{claim_id}`
- THEN the page SHALL display a "Grouped Data" card
- AND the card SHALL show the external_reference, description, notes, and batch creation date
- AND the SOS Records table SHALL NOT render

### Requirement: Detail Page UI Sections

The page at `/gestiones/{id}` SHALL render sections based on claim type:

**Section 1 — Claim Header (all types):** Displays claim type badge, claimer_name (asegurado), policy_number (póliza), plate (patente), claimed_amount (monto), group name, and claim kind name. Online gestion/reference display: SOS claims show `gestion`; Grouped claims show `external_reference` from the linked batch.

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

## Non-Functional Requirements

- **N+1 guard**: The use case SHALL execute exactly the minimum repository calls — one per data source. No additional queries SHALL be issued per SosClaim or per Payment.
- **Error notifications**: All errors SHALL surface via `ui.notify` — never silent failures or raw tracebacks.
- **Back navigation**: Every detail page SHALL provide a visible back link to `/gestiones`.

## Out of Scope (v2+)

- Document gallery display
- Agent name resolution in payments (raw IDs shown)
- Payment via name resolution (raw IDs shown)
- Inline editing of claim or SosClaim fields
- Payment CRUD operations from the detail page
- SosClaim creation or modification
