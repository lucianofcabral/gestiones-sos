# NcPayment (CreditNote) CRUD Specification

## Purpose

Full CRUD lifecycle for CreditNote entities linked to Payments and Periods — create, query, update, mark delivered, and soft-delete.

## Requirements

### Requirement: Create NcPayment

The system MUST create a CreditNote with fields: nc_payment_id, payment_id, period_id, delivered (default False), created_date, active (default True).

#### Scenario: Create NcPayment for a period
- GIVEN valid payment_id and period_id
- WHEN the use case executes
- THEN the system creates the CreditNote with `delivered=False`, `active=True`
- AND returns it with a generated `nc_payment_id`

### Requirement: Get NcPayment by ID

The system MUST return a CreditNote by `nc_payment_id`, or `None` if not found.

#### Scenario: NcPayment exists
- GIVEN a CreditNote exists
- WHEN the use case executes with its `nc_payment_id`
- THEN the system returns the matching CreditNote

#### Scenario: NcPayment not found
- GIVEN no CreditNote for the given `nc_payment_id`
- WHEN the use case executes
- THEN the system returns `None`

### Requirement: List All NcPayments

The system MUST return all CreditNotes (active and inactive).

#### Scenario: Multiple NcPayments exist
- GIVEN several CreditNotes in the store
- WHEN the use case executes
- THEN the system returns the full list

### Requirement: Update NcPayment

The system MUST update non-identity fields (not `nc_payment_id`) by `nc_payment_id`. Returns `True` on success, `False` if not found. The `delivered` field MUST NOT be updatable via generic update — use `mark_delivered` instead.

#### Scenario: Update period_id
- GIVEN a CreditNote exists
- WHEN the use case executes with a new `period_id`
- THEN the system updates the field and returns `True`

#### Scenario: Update non-existent NcPayment
- GIVEN no CreditNote for the given `nc_payment_id`
- WHEN the use case executes
- THEN the system returns `False`

### Requirement: Mark Delivered

The system MUST provide a dedicated `mark_delivered(nc_payment_id)` operation that sets `delivered=True`. Returns `True` on success, `False` if not found.

#### Scenario: Mark existing NcPayment delivered
- GIVEN a CreditNote with `delivered=False`
- WHEN `mark_delivered` is called with its `nc_payment_id`
- THEN the system sets `delivered=True` and returns `True`

#### Scenario: Mark non-existent NcPayment
- GIVEN no CreditNote for the given `nc_payment_id`
- WHEN `mark_delivered` is called
- THEN the system returns `False`

### Requirement: Inactivate NcPayment

The system MUST set `active=False` on a CreditNote by `nc_payment_id`.

#### Scenario: Inactivate existing NcPayment
- GIVEN a CreditNote with `active=True`
- WHEN the use case executes
- THEN the system sets `active=False`

### Requirement: Activate NcPayment

The system MUST set `active=True` on a CreditNote by `nc_payment_id`.

#### Scenario: Activate existing NcPayment
- GIVEN a CreditNote with `active=False`
- WHEN the use case executes
- THEN the system sets `active=True`
