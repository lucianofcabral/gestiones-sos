# Claim-Listing Specification

## Purpose

The claim-listing capability provides a centralized view of all claims ("gestiones") at `/gestiones`. It fetches Claims and SosClaims from their respective repositories, joins them in-memory by claim ID, and displays a sortable, refreshable table with active/inactive filtering and soft-delete support.

## Requirements

### Requirement: Listar Gestiones

The system SHALL provide a page at `/gestiones` that fetches all Claims and SosClaims and joins them on claim ID, returning `list[ClaimDetailDTO]`. The table SHALL display these columns: gestion (SosClaim number), claimer_name, policy_number, plate, claimed_amount, category, reason, status, load_user, created_at, solved, active.

The `ObtenerGestiones` use case SHALL call `claim_repo.get_all()` and `sos_claim_repo.get_all()` and join in-memory by claim ID. No changes to repositories or ports are required.

#### Scenario: List with active claims

- GIVEN the database contains active claims with associated SosClaims
- WHEN the user navigates to `/gestiones`
- THEN the table SHALL display all active claims with their SOS data
- AND each row SHALL show all columns with correct values

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

Each row SHALL provide a delete button that calls the existing `EliminarGestionSOS` use case for soft-deletion. The action SHALL require user confirmation before proceeding. On success the table SHALL refresh. If the claim has active payments, `EliminarGestionSOS` SHALL reject the operation and the system SHALL display the error via `ui.notify`.

#### Scenario: Delete active claim

- GIVEN a visible active claim in the table
- WHEN the user clicks delete and confirms
- THEN the claim SHALL become inactive (soft-deleted)
- AND the table SHALL refresh, removing it from the active-only view

#### Scenario: Delete already inactive claim

- GIVEN an inactive claim visible with the toggle enabled
- WHEN the user clicks delete and confirms
- THEN `EliminarGestionSOS` SHALL execute idempotently without error
- AND the table SHALL refresh

#### Scenario: Cannot delete claim with active payments

- GIVEN a claim with active payments
- WHEN the user attempts to delete it
- THEN the system SHALL show a `ui.notify` error message
- AND the claim SHALL remain active in the table

### Requirement: Error States

#### Scenario: Database connection failure

- GIVEN the database is unreachable
- WHEN the user navigates to `/gestiones`
- THEN the system SHALL display an error via `ui.notify`
- AND the table SHALL remain empty or show the previous state
