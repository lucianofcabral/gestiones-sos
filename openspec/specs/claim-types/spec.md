# Claim-Types Specification

## Purpose

The claim-types capability defines the polymorphic Claim model. A single `Claim` record uses a `ClaimKind` discriminator to determine its type-specific behavior — data, form, list display, and detail rendering. New claim types can be added without touching existing code, following the registration-use-case + DTO + detail-serializer contract.

## Discriminator

`Claim.claim_kind_id` (FK to `ClaimKind`) acts as the discriminator. Recognized `ClaimKind` values: `sos`, `grouped`, `tres_arroyos`, `adhoc`. Only `sos` and `grouped` have active forms in v1.

## Requirements

### Requirement: Polymorphic Model

The system SHALL distinguish claim types via `Claim.claim_kind_id`. Each claim SHALL have exactly one type. The `Claim` base record SHALL hold shared fields (claimer_name, policy_number, plate, claimed_amount, group_id, comment, created_at, active).

#### Scenario: SOS claim created with standard fields

- GIVEN an agent submits an SOS claim form
- WHEN the system creates the claim
- THEN a `Claim` record SHALL be created with `claim_kind_id` = sos
- AND a `SosClaim` record SHALL be created with FK to the new Claim
- AND `SosClaim.gestion` SHALL be a required positive integer

#### Scenario: Grouped claim created without gestion

- GIVEN an agent submits a Grouped batch claim form
- WHEN the system creates the claim
- THEN a `Claim` record SHALL be created with `claim_kind_id` = grouped
- AND a `GroupedClaim` record SHALL be created with FK to the new Claim
- AND `GroupedClaim.notes` SHALL be optional text
- AND `GroupedClaim` SHALL have NO `gestion` field
- AND `GroupedClaim` SHALL reference a `GroupClaim` batch via FK

### Requirement: GroupClaim as Batch Entity

`GroupClaim` SHALL be repurposed from a simple name lookup to a batch entity with `external_reference` (required text, unique), `description` (optional text), and `created_at` (auto timestamp). Existing rows SHALL have `external_reference` set to their `name` via migration.

#### Scenario: Batch entity creation

- GIVEN an agent creates a new group claim batch
- WHEN the system persists the `GroupClaim`
- THEN `external_reference` SHALL be required and unique
- AND `description` SHALL be optional
- AND `created_at` SHALL be auto-populated

#### Scenario: Migration of existing rows

- GIVEN existing `GroupClaim` rows with `name = "Lote 2024-001"`
- WHEN the migration runs
- THEN each row SHALL have `external_reference = "Lote 2024-001"`
- AND `name` SHALL remain unchanged
- AND `description` SHALL be NULL

### Requirement: Extensibility Contract

Adding a new claim type SHALL require: (1) a new `ClaimKind` seed value, (2) a new type-specific table with FK to `Claim`, (3) a new registration use case, (4) a new DTO, and (5) a detail serializer. No changes to the discriminator dispatch or base `Claim` model SHALL be needed.

#### Scenario: New claim type "adhoc" added

- GIVEN a developer adds `ClaimKind.adhoc` and an `AdhocClaim` table
- WHEN the system dispatches by `claim_kind_id` = adhoc
- THEN the system SHALL render the adhoc-specific form
- AND the list SHALL show adhoc rows with their type column
- AND the detail SHALL render the adhoc-specific section
