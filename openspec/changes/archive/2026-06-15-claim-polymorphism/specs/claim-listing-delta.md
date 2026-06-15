# Delta for Claim-Listing

## ADDED Requirements

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

## MODIFIED Requirements

### Requirement: Listar Gestiones

The system SHALL provide a page at `/gestiones` that fetches all Claims, SosClaims, and GroupedClaims, joining on claim ID and returning `list[ClaimDetailDTO]`. The table SHALL display these columns: type, gestion_or_reference, claimer_name, policy_number, plate, claimed_amount, category (SOS only), reason (SOS only), status, load_user, created_at, solved, active.

`ObtenerGestiones` SHALL call `claim_repo.get_all()`, `sos_claim_repo.get_all()`, and `grouped_claim_repo.get_all()` and join in-memory by claim ID. The `gestion` column SHALL display `SosClaim.gestion` for SOS rows and `GroupClaim.external_reference` for Grouped rows. For Grouped rows, category and reason SHALL display "—".

(Previously: only SosClaims were fetched; gestion always displayed SosClaim.gestion)

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

### Requirement: Eliminar Gestión

Each row SHALL provide a delete button that dispatches to the per-type delete use case — `EliminarGestionSOS` for SOS claims, `EliminarGroupedClaim` for Grouped claims. Both SHALL soft-delete the claim. The action SHALL require user confirmation. On success the table SHALL refresh.

(Previously: only `EliminarGestionSOS` was called — no type dispatch)

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

### Requirement: Sort fallback for Grouped rows

The system SHOULD sort by `created_at` as fallback for Grouped rows where `gestion` is null.

(Previously: sorting relied solely on `gestion` — now needs fallback for null values)

#### Scenario: Sort without gestion values

- GIVEN the table includes Grouped claims with no `gestion` field
- WHEN the user sorts by the gestion/reference column
- THEN rows SHALL be ordered by `created_at` descending when `gestion` is null
