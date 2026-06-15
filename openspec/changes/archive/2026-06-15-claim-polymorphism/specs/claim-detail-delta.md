# Delta for Claim-Detail

## ADDED Requirements

### Requirement: Grouped Claim Batch Card

The detail page SHALL render a "Grouped Data" card for claims of type `grouped`. The card SHALL display: `GroupClaim.external_reference`, `GroupClaim.description` (or "—" if null), `GroupedClaim.notes` (or "—" if null), and batch creation date.

#### Scenario: Grouped claim shows batch info

- GIVEN a claim of type `grouped` linked to a batch with external_reference="Lote-2024-001"
- WHEN the agent navigates to `/gestiones/{claim_id}`
- THEN the page SHALL display a "Grouped Data" card
- AND the card SHALL show the external_reference, description, notes, and batch creation date
- AND the SOS Records table SHALL NOT render

## MODIFIED Requirements

### Requirement: Obtener Gestion Por ID

The system SHALL provide a use case `ObtenerGestionPorId` that accepts a `claim_id` UUID and fetches the `Claim` by ID. Based on `Claim.claim_kind_id`, it SHALL fetch either `SosClaim` records (for SOS type) or `GroupedClaim` + `GroupClaim` batch (for Grouped type). In all cases, it SHALL fetch the `ClaimKind` name and all `Payment` records.

If the claim is not found, the use case SHALL raise `ClaimNotFoundError`.

(Previously: always fetched SosClaim records via `SosClaimRepoPort` — now type-dispatched)

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

#### Scenario: Claim not found

- GIVEN a claim ID does not exist in the database
- WHEN the agent navigates to `/gestiones/{non_existent_id}`
- THEN the system SHALL NOT render a detail page
- AND the system SHALL display a `ui.notify` error
- AND the system SHALL redirect to `/gestiones`

### Requirement: Detail Page UI Sections

The page at `/gestiones/{id}` SHALL render sections based on claim type:

**Section 1 — Claim Header (all types):** Displays claim type badge, claimer_name (asegurado), policy_number (póliza), plate (patente), claimed_amount (monto), group name, and claim kind name. Online gestion/reference display: SOS claims show `gestion`; Grouped claims show `external_reference` from the linked batch.

**Section 2a — SOS Records Table (SOS type only):** Displays all SosClaim records with columns: gestion, category, reason, status, load_user, response_user, itr. If no records exist, shows empty-state label.

**Section 2b — Grouped Data Card (Grouped type only):** Displays batch external_reference, description, notes, and creation date.

**Section 3 — Payments Table (all types):** Displays payments with columns: amount, created_date, payer_id, payee_id, payment_via_id.

(Previously: fixed three sections always rendering SOS Records Table — now Section 2 is type-dependent)

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
