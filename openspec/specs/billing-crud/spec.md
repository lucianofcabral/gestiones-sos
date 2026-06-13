# Billing CRUD Specification

## Purpose

CRUD lifecycle for Invoice entities — create, list by period, view by ID, delete with referential integrity, and calculate period billing totals. Invoices represent billing documents issued by SOS against a period.

## Requirements

### Requirement: Create Invoice

The system MUST create an Invoice with: `invoice_id` (UUID, auto-generated), `invoice_number` (string, non-empty, from SOS), `period_id` (UUID, FK to existing period), `emited_date` (datetime), `amount` (float, >0), `created_at` (datetime, auto-generated).

#### Scenario: Happy path
- GIVEN an existing Period
- WHEN `add` is called with `invoice_number="F001-2024"`, a valid `period_id`, `emited_date`, and `amount=1500.00`
- THEN the system creates and returns an Invoice with those values, auto-generating `invoice_id` and `created_at`

#### Scenario: Foreign key violation
- GIVEN no Period for the given `period_id`
- WHEN `add` is called with a non-existent `period_id`
- THEN the system raises an integrity error

### Requirement: List Invoices

The system MUST return all Invoices, optionally filtered by `period_id`.

#### Scenario: All invoices
- GIVEN multiple Invoices across different periods
- WHEN `get_all` is called
- THEN the system returns all Invoices

#### Scenario: By period
- GIVEN Invoices for Period A and Period B
- WHEN `get_by_period_id(period_A_id)` is called
- THEN the system returns only Invoices for Period A

#### Scenario: Empty store
- GIVEN no Invoices in the store
- WHEN `get_all` is called
- THEN the system returns an empty list

### Requirement: Get Invoice by ID

The system MUST return an Invoice by `invoice_id`, or `None` if not found.

#### Scenario: Found
- GIVEN an existing Invoice
- WHEN `get_by_id(invoice_id)` is called
- THEN the system returns the matching Invoice

#### Scenario: Not found
- GIVEN no Invoice for the given `invoice_id`
- WHEN `get_by_id(invoice_id)` is called
- THEN the system returns `None`

### Requirement: Delete Invoice

The system MUST delete an Invoice by `invoice_id`. It MUST NOT delete if any DocumentEntity references this `invoice_id` with `entity_type=INVOICE`.

#### Scenario: No documents attached
- GIVEN an Invoice with no DocumentEntity referencing it
- WHEN `delete(invoice_id)` is called
- THEN the system deletes the Invoice

#### Scenario: Non-existent invoice
- GIVEN no Invoice for the given `invoice_id`
- WHEN `delete(invoice_id)` is called
- THEN the system does nothing (no-op)

#### Scenario: Documents attached
- GIVEN an Invoice with DocumentEntity records referencing its `invoice_id`
- WHEN `delete(invoice_id)` is called
- THEN the system raises `ValueError` and does NOT delete

### Requirement: Calculate Total Billing by Year/Month

The system MUST return the sum of all Invoice amounts for the given `year` and `month`, or `0.0` if none exist.

#### Scenario: Invoices found
- GIVEN Invoices with amounts 1000.00 and 500.00 for year=2024, month=6
- WHEN `get_total_billing_by_year_month(2024, 6)` is called
- THEN the system returns 1500.00

#### Scenario: No invoices for period
- GIVEN no Invoices for year=2024, month=7
- WHEN `get_total_billing_by_year_month(2024, 7)` is called
- THEN the system returns 0.0

## Domain Changes

- `Invoice.invoice_number`: `int` → `str` (external code from SOS, not auto-generated)

## Out of Scope
- Invoice editing (delete + re-create instead)
- Document attachment per invoice (exists separately via `DocumentEntity`)
- PDF generation or emission
- Auto-generation from NC aggregation
- Invoice vs credit note reconciliation
