# Claim-Registration Specification

## Purpose

The claim-registration capability provides a form at `/gestiones/nueva` for agents to register SOS claims atomically — creating both a `Claim` (base) and `SosClaim` (SOS-specific) in a single database transaction via `RegistrarGestionSOS`.

## Requirements

### Requirement: Form Layout

The system SHALL render a page at `/gestiones/nueva` with two card sections using NiceGUI components.

**Claim Data** card — claim_kind (dropdown), group (dropdown), claimer_name (text), policy_number (text), plate (text), claimed_amount (number), comment (textarea).

**SOS Data** card — gestion (number), category (text), reason (text), load_user (text), response_user (text), status (dropdown), itr (number).

#### Scenario: Form renders with both cards

- GIVEN the agent navigates to `/gestiones/nueva`
- THEN the page SHALL display a "Claim Data" card and a "SOS Data" card
- AND all specified fields SHALL be present in their respective cards

### Requirement: Dropdown Data Loading

The system SHALL load claim_kind options via `ObtenerClaimKinds` and group options via `ObtenerGrupos` synchronously on page init. Both dropdowns SHALL display all records from the database, including inactive ones.

#### Scenario: Dropdowns populated on page load

- GIVEN the database contains claim kinds and groups (some inactive)
- WHEN the agent navigates to `/gestiones/nueva`
- THEN the claim_kind dropdown SHALL list all claim kinds including inactive
- AND the group dropdown SHALL list all groups including inactive

### Requirement: Status Field

The status field SHALL be a dropdown with exactly three options: `CERRADO`, `ABIERTO`, `RECHAZADO`.

#### Scenario: Status dropdown shows three options

- GIVEN the agent is on the form page
- THEN the status dropdown SHALL present `CERRADO`, `ABIERTO`, `RECHAZADO`

### Requirement: Client-Side Validation

Before submission, the system SHALL validate: gestion (required, positive integer), claim_kind_id (required), group_id (required), claimer_name (required, non-empty), policy_number (required, non-empty), plate (required, non-empty). On validation failure, the system SHALL notify the agent via `ui.notify` and SHALL NOT invoke the use case.

#### Scenario: Missing required fields blocked

- GIVEN the agent submits the form with empty required fields
- THEN the system SHALL display validation errors via `ui.notify`
- AND the use case SHALL NOT be called

### Requirement: Successful Registration

On valid submission, the system SHALL call `RegistrarGestionSOS` with form data. On success, the system SHALL display a positive notification and redirect to `/gestiones`.

#### Scenario: Happy path — claim created and redirected

- GIVEN the agent fills all fields with valid data
- WHEN the agent clicks submit
- THEN a Claim and SosClaim SHALL be created atomically via the UOW
- AND the agent SHALL see a positive `ui.notify` confirming the registration
- AND the system SHALL navigate to `/gestiones`

### Requirement: Duplicate Gestion Handling

If `RegistrarGestionSOS` raises `GestionAlreadyExistsError`, the system SHALL catch it and display the error message via `ui.notify` (type=negative). The form SHALL retain all entered values so the agent can correct the gestion number.

#### Scenario: Duplicate gestion number shows error

- GIVEN a SosClaim with gestion number 999 already exists
- WHEN the agent submits the form with gestion=999
- THEN the system SHALL display "Ya existe una gestión con el número 999" via `ui.notify`
- AND the form SHALL retain all entered values
- AND no new records SHALL be created

### Requirement: Server Error Handling

If the use case raises any other exception, the system SHALL catch it and display a generic error via `ui.notify` (type=negative).

#### Scenario: Database connection failure

- GIVEN the database is unreachable
- WHEN the agent submits the form
- THEN the system SHALL display "Error al registrar gestión" via `ui.notify`
- AND the agent SHALL remain on the form page
