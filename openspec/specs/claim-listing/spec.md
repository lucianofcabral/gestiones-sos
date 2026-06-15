# Claim-Listing Specification

## Purpose

The claim-listing capability provides a centralized view of all claims ("gestiones") at `/gestiones`. It fetches Claims, SosClaims, and GroupedClaims from their respective repositories, joins them in-memory by claim ID, and displays a sortable, refreshable table with type-discriminated columns, active/inactive filtering, and soft-delete support.

## Requirements

### Requirement: Type Column

The `/gestiones` table SHALL include a `type` column as the first column. The column SHALL display the `ClaimKind` display name (e.g., "SOS", "Grouped", "Tres Arroyos", "Ad-Hoc").

#### Scenario: Type column visible for all rows

- GIVEN the table displays claims of different types
- THEN each row SHALL have a "Tipo" column as the first column
- AND the value SHALL match the claim's `ClaimKind` display name

#### Scenario: Type column on empty table

- GIVEN no claims exist
- WHEN the table shows the empty state
- THEN the column headers SHALL still include the "Tipo" column

### Requirement: Listar Gestiones

The system SHALL provide a page at `/gestiones` that fetches all Claims, SosClaims, and GroupedClaims, joining on claim ID and returning `list[ClaimDetailDTO]`. The table SHALL display these columns: type, gestion_or_reference, claimer_name, policy_number, plate, claimed_amount, category (SOS only), reason (SOS only), status, load_user, created_at, solved, active.

`ObtenerGestiones` SHALL call `claim_repo.get_all()`, `sos_claim_repo.get_all()`, and `grouped_claim_repo.get_all()` and join in-memory by claim ID. The `gestion` column SHALL display `SosClaim.gestion` for SOS rows and `GroupClaim.external_reference` for Grouped rows. For Grouped rows, category and reason SHALL display "—".

#### Scenario: List with active claims

- GIVEN the database contains active claims with associated SosClaims
- WHEN the user navigates to `/gestiones`
- THEN the table SHALL display all active claims with their SOS data
- AND each row SHALL show all columns with correct values

#### Scenario: SOS rows display gestion number

- GIVEN the database contains an SOS claim with gestion=12345
- WHEN the user navigates to `/gestiones`
- THEN the "gestion" column for that row SHALL display "12345"
- AND category and reason SHALL display their values

#### Scenario: Grouped rows display external_reference

- GIVEN the database contains a Grouped claim linked to a batch with external_reference="Lote-2024-001"
- WHEN the user navigates to `/gestiones`
- THEN the "gestion" column for that row SHALL display "Lote-2024-001"
- AND category and reason SHALL display "—"

#### Scenario: Mixed list shows both types correctly

- GIVEN claims of both SOS and Grouped types exist
- WHEN the user navigates to `/gestiones`
- THEN each row SHALL display its type column
- AND SOS rows SHALL show their gestion in the gestion column
- AND Grouped rows SHALL show their external_reference in the gestion column

#### Scenario: Empty list when no claims exist

- GIVEN no claims exist in the database
- WHEN the user navigates to `/gestiones`
- THEN the table SHALL display an empty state with a "No se encontraron gestiones" message

### Requirement: Active/Inactive Filter

The system SHALL default to showing only active claims. The system SHALL provide a toggle control (switch or checkbox) that, when enabled, includes inactive claims in the table. Toggling SHALL trigger a table refresh.

#### Scenario: Toggle to show inactive claims

- GIVEN the user is viewing the table with the active-only filter
- WHEN the user enables the "Mostrar inactivos" toggle
- THEN the table SHALL refresh and include both active and inactive claims

#### Scenario: Default view shows only active claims

- GIVEN the user navigates to `/gestiones` for the first time
- THEN the filter SHALL default to active-only
- AND inactive claims SHALL NOT appear in the table

### Requirement: Eliminar Gestión

Each row SHALL provide a delete button that dispatches to the per-type delete use case — `EliminarGestionSOS` for SOS claims, `EliminarGroupedClaim` for Grouped claims. Both SHALL soft-delete the claim. The action SHALL require user confirmation. On success the table SHALL refresh. If the claim has active payments, the use case SHALL reject the operation and the system SHALL display the error via `ui.notify`.

#### Scenario: Delete SOS claim

- GIVEN a visible active SOS claim in the table
- WHEN the user clicks delete and confirms
- THEN `EliminarGestionSOS` SHALL be called
- AND the claim SHALL become inactive (soft-deleted)
- AND the table SHALL refresh

#### Scenario: Delete Grouped claim

- GIVEN a visible active Grouped claim in the table
- WHEN the user clicks delete and confirms
- THEN `EliminarGroupedClaim` SHALL be called
- AND the claim SHALL become inactive (soft-deleted)
- AND the table SHALL refresh

#### Scenario: Delete already inactive claim

- GIVEN an inactive claim visible with the toggle enabled
- WHEN the user clicks delete and confirms
- THEN the per-type delete use case SHALL execute idempotently without error
- AND the table SHALL refresh

#### Scenario: Cannot delete claim with active payments

- GIVEN a claim with active payments
- WHEN the user attempts to delete it
- THEN the system SHALL show a `ui.notify` error message
- AND the claim SHALL remain active in the table

### Requirement: Sort Fallback for Grouped Rows

The system SHOULD sort by `created_at` as fallback for Grouped rows where `gestion` is null.

#### Scenario: Sort without gestion values

- GIVEN the table includes Grouped claims with no `gestion` field
- WHEN the user sorts by the gestion/reference column
- THEN rows SHALL be ordered by `created_at` descending when `gestion` is null

### Requirement: Error States

#### Scenario: Database connection failure

- GIVEN the database is unreachable
- WHEN the user navigates to `/gestiones`
- THEN the system SHALL display an error via `ui.notify`
- AND the table SHALL remain empty or show the previous state

### Requirement: Post-Registration Redirect

The system SHALL navigate to `/gestiones` after a successful registration from `/gestiones/nueva`. The redirected page SHALL display the newly created claim in the table. A positive notification SHALL confirm the result.

#### Scenario: New claim visible after registration redirect

- GIVEN the agent successfully registers a new claim
- WHEN the system redirects to `/gestiones`
- THEN the table SHALL include the newly created claim
- AND a positive `ui.notify` SHALL confirm the registration

### Requirement: Navigate to Claim Detail

Each row in the `/gestiones` table SHALL be clickable. When clicked, the system SHALL navigate to `/gestiones/{claim_id}` to display the full claim detail page. The click target SHALL be the entire row — not just a specific button or cell.

#### Scenario: Row click navigates to detail

- GIVEN the agent is viewing the gestiones list at `/gestiones`
- WHEN the agent clicks any row in the table
- THEN the system SHALL navigate to `/gestiones/{claim_id}` for that row's claim

#### Scenario: Navigation preserves back context

- GIVEN the agent navigates from `/gestiones` to `/gestiones/{claim_id}`
- WHEN the agent clicks the back link on the detail page
- THEN the system SHALL return to `/gestiones` with the same active/inactive filter state
