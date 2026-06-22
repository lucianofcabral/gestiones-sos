# Claim-Registration Specification

## Purpose

The claim-registration capability provides a form at `/gestiones/nueva` for agents to register claims atomically — creating both a `Claim` (base) and a type-specific record (`SosClaim` or `GroupedClaim`) in a single database transaction. The form dynamically adapts to the selected `ClaimKind`: SOS claims follow the existing SOS workflow; Grouped claims link to a batch without an individual `gestion`.

## Requirements

### Requirement: Claim Type Selector

The system SHALL render a claim type selector at the top of `/gestiones/nueva` before displaying any data cards. The selector SHALL be a dropdown labeled "Tipo de Gestión" populated with eligible `ClaimKind` values. The form content SHALL mutate based on the selected type — no card sections SHALL render until a type is chosen.

#### Scenario: Type selector renders on page load

- GIVEN the agent navigates to `/gestiones/nueva`
- THEN a "Tipo de Gestión" dropdown SHALL be visible
- AND options SHALL include "SOS" and "Grouped" at minimum
- AND no data cards SHALL be visible until a type is selected

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

### Requirement: Conditional Form Sections

When "SOS" is selected, the system SHALL render the existing "Claim Data" + "SOS Data" cards. When "Grouped" is selected, the system SHALL render the "Claim Data" card (excluding `claim_kind` dropdown) and a "Grouped Data" card with fields: `group_claim_id` (dropdown of batches), `notes` (textarea, optional).

#### Scenario: SOS type shows SOS card

- GIVEN the agent selects "SOS" from the type selector
- THEN a "Claim Data" card SHALL display with all shared fields
- AND an "SOS Data" card SHALL display with gestion, category, reason, load_user, response_user, status, itr
- AND `gestion` SHALL be required

#### Scenario: Grouped type shows Grouped card

- GIVEN the agent selects "Grouped" from the type selector
- THEN a "Grouped Data" card SHALL display with `group_claim_id` (dropdown) and `notes` (textarea)
- AND the form SHALL NOT display gestion, category, reason, load_user, response_user, itr fields
- AND `group_claim_id` SHALL be required

#### Scenario: Switching type clears conditional fields

- GIVEN the agent has filled SOS Data fields
- WHEN the agent switches the type selector to "Grouped"
- THEN all SOS Data field values SHALL be cleared
- AND the "Grouped Data" card SHALL appear in place of the "SOS Data" card

### Requirement: GroupClaim Batch Dropdown

The `group_claim_id` dropdown SHALL list active `GroupClaim` batches by their `external_reference` identifier.

#### Scenario: Batches listed in dropdown

- GIVEN the database contains GroupClaim batches with external_references
- WHEN the agent selects "Grouped" as the claim type
- THEN the `group_claim_id` dropdown SHALL list each batch by its `external_reference`
- AND inactive batches SHALL NOT appear

### Requirement: Successful Registration

On valid submission, the system SHALL call the use case corresponding to the selected claim type — `RegistrarGestionSOS` for SOS claims, or `RegistrarGroupedClaim` for Grouped claims. Both use cases SHALL atomically create a `Claim` + type-specific record via the UOW. On success, the system SHALL display a positive notification and redirect to `/gestiones`.

#### Scenario: Happy path — SOS claim created and redirected

- GIVEN the agent selects "SOS" and fills all required fields with valid data
- WHEN the agent clicks submit
- THEN `RegistrarGestionSOS` SHALL be called
- AND a Claim and SosClaim SHALL be created atomically via the UOW
- AND the agent SHALL see a positive `ui.notify`
- AND the system SHALL navigate to `/gestiones`

#### Scenario: Happy path — Grouped claim created and redirected

- GIVEN the agent selects "Grouped" and fills all required fields
- WHEN the agent clicks submit
- THEN `RegistrarGroupedClaim` SHALL be called
- AND a Claim and GroupedClaim SHALL be created atomically via the UOW
- AND the GroupedClaim SHALL reference the selected GroupClaim batch
- AND the agent SHALL see a positive `ui.notify`
- AND the system SHALL navigate to `/gestiones`

### Requirement: Client-Side Validation

Before submission, the system SHALL validate: claim_kind_id (required), group_id (required), claimer_name (required, non-empty), policy_number (required, non-empty), plate (required, non-empty). For SOS type only: gestion (required, positive integer). For Grouped type only: group_claim_id (required). On validation failure, the system SHALL notify the agent via `ui.notify` and SHALL NOT invoke the use case.

#### Scenario: Missing SOS fields blocked

- GIVEN the agent submits SOS form with empty required fields
- THEN the system SHALL display validation errors via `ui.notify`
- AND the use case SHALL NOT be called

#### Scenario: Missing Grouped fields blocked

- GIVEN the agent selects "Grouped" and submits with empty `group_claim_id`
- THEN the system SHALL display validation errors via `ui.notify`
- AND `RegistrarGroupedClaim` SHALL NOT be called

### Requirement: Duplicate Gestion Handling

Applies only to SOS claims. If `RegistrarGestionSOS` raises `GestionAlreadyExistsError`, the system SHALL catch it and display the error message via `ui.notify` (type=negative). The form SHALL retain all entered values so the agent can correct the gestion number. For Grouped claims, gestion does not exist so this error cannot occur.

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
