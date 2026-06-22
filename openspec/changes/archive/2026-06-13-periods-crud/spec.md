# Periods CRUD Specification

## Purpose

CRUD lifecycle for Period entities — create with duplicate guard, list all ordered by recency, and delete with referential integrity against invoices and credit notes (NCs). Periods are the temporal anchor for billing documents.

## Requirements

### Requirement: Create Period

The system MUST create a Period with: `period_id` (UUID, auto-generated), `year` (int), `month` (int), `created_at` (datetime, auto-generated). The system MUST reject creation if a Period with the same `(year, month)` already exists.

#### Scenario: Happy path

- GIVEN no Period for year=2024, month=6
- WHEN the system creates a Period with `year=2024, month=6`
- THEN the system returns a Period with those values, auto-generating `period_id` and `created_at`

#### Scenario: Duplicate (year, month)

- GIVEN a Period already exists for year=2024, month=6
- WHEN the system attempts to create another Period with `year=2024, month=6`
- THEN the system raises `ValueError` with a message indicating the duplicate

### Requirement: List Periods

The system MUST return all Periods ordered by year DESC, month DESC, or an empty list if none exist.

#### Scenario: Periods exist

- GIVEN Periods for (2024, 6), (2024, 3), and (2023, 12)
- WHEN `get_all` is called
- THEN the system returns them ordered: (2024, 6), (2024, 3), (2023, 12)

#### Scenario: No periods

- GIVEN no Periods in the store
- WHEN `get_all` is called
- THEN the system returns an empty list

### Requirement: Delete Period

The system MUST delete a Period by `period_id`. It MUST NOT delete if the Period has associated Invoices (`billing_repo.get_by_period_id` returns non-empty) or associated CreditNotes (`nc_payment_repo.get_by_period_id` returns non-empty). If the Period does not exist, the system MUST return `False` (no-op).

#### Scenario: No dependents

- GIVEN a Period with no Invoices and no CreditNotes referencing it
- WHEN `delete(period_id)` is called
- THEN the system deletes the Period and returns `True`

#### Scenario: Non-existent period

- GIVEN no Period for the given `period_id`
- WHEN `delete(period_id)` is called
- THEN the system does nothing and returns `False`

#### Scenario: Period has invoices

- GIVEN a Period with at least one Invoice referencing its `period_id`
- WHEN `delete(period_id)` is called
- THEN the system raises `ValueError` indicating invoices block deletion
- AND the Period is NOT deleted

#### Scenario: Period has credit notes

- GIVEN a Period with at least one CreditNote referencing its `period_id`
- WHEN `delete(period_id)` is called
- THEN the system raises `ValueError` indicating credit notes block deletion
- AND the Period is NOT deleted

## Domain Changes

- Add `UniqueConstraint('year', 'month')` to the `periods` table definition and via Alembic migration

## Out of Scope

- Edit or update (year/month identify the period — delete + re-create instead)
- Period properties are computed from `year` and `month`, no persistence changes needed
- Wiring, UI, or container configuration (use case layer only)
