# Home Page Specification — Metrics & Content

## Purpose

Replace the existing module-card home page with a dashboard showing operational metrics: total claims count, recent claims, and stat cards for pending SOS, active payments, and current period.

## Requirements

### Requirement: Total Claims Counter

The system MUST display the total number of claims stored in the database on the home page.

#### Scenario: Claims exist
- GIVEN the database contains N claims
- WHEN the home page renders
- THEN the system displays "Total Siniestros: N"

#### Scenario: No claims
- GIVEN the database contains zero claims
- WHEN the home page renders
- THEN the system displays "Total Siniestros: 0" or a zero-state message

### Requirement: Recent 5 Claims Table

The system MUST display the 5 most recent claims (by `created_at` descending) showing: claimer name, policy number, plate, and creation date.

#### Scenario: Five or more claims exist
- GIVEN at least 5 claims in the database
- WHEN the home page renders
- THEN the system shows a table with the 5 most recent claims
- AND each row shows claimer_name, policy_number, plate, created_at

#### Scenario: Fewer than 5 claims exist
- GIVEN fewer than 5 claims in the database
- WHEN the home page renders
- THEN the system shows all available claims in the table (no padding with empty rows)

#### Scenario: No claims
- GIVEN zero claims in the database
- WHEN the home page renders
- THEN the system shows an empty-state message ("No hay siniestros registrados")

### Requirement: Stat Cards

The system MUST display three stat cards: pending SOS claims, active payments, and current period name.

#### Scenario: All stats have data
- GIVEN pending SOS claims exist, active payments exist, and a current period is set
- WHEN the home page renders
- THEN three stat cards show the respective values

#### Scenario: Some stats are zero or absent
- GIVEN no pending SOS claims, no active payments, or no current period
- WHEN the home page renders
- THEN the affected stat card displays "0" or "—" for the missing value
- AND the card still renders without error

#### Scenario: All stats empty
- GIVEN empty database
- WHEN the home page renders
- THEN all three stat cards show zero/empty values
- AND the page does not crash
