# Payment Inactivation Rule Specification

## Purpose

Domain service that determines whether a Payment can be inactivated based on credit-note and billing lifecycle rules.

## Requirements

### Requirement: Evaluate Inactivation Eligibility

The `CanInactivatePaymentService` MUST evaluate a Payment's inactivation eligibility. It SHALL accept an `NcPaymentRepoPort` and `BillingRepoPort` (with `get_by_period_id`).

Logic:
1. No NcPayment for `payment_id` → CAN inactivate
2. NcPayment exists AND its period has zero Invoices → CAN inactivate
3. NcPayment exists AND its period has ≥1 Invoice → CANNOT inactivate (period closed)

The service MUST return `(can_inactivate: bool, reason: str)`.

#### Scenario: No NcPayment — can inactivate
- GIVEN `NcPaymentRepoPort.get_by_payment_id()` returns `None`
- WHEN the service evaluates
- THEN it returns `(True, "No NcPayment found for this payment")`

#### Scenario: NcPayment without Invoice — can inactivate
- GIVEN `NcPaymentRepoPort.get_by_payment_id()` returns an NcPayment
- AND `BillingRepoPort.get_by_period_id(nc.period_id)` returns `[]`
- WHEN the service evaluates
- THEN it returns `(True, "Period has no invoices")`

#### Scenario: NcPayment with Invoice — cannot inactivate
- GIVEN `NcPaymentRepoPort.get_by_payment_id()` returns an NcPayment
- AND `BillingRepoPort.get_by_period_id(nc.period_id)` returns one or more Invoices
- WHEN the service evaluates
- THEN it returns `(False, "Period is closed, cannot inactivate")`

### Requirement: Add get_by_period_id to BillingRepoPort

`BillingRepoPort` MUST gain `get_by_period_id(period_id: UUID) -> list[Invoice]`. Both `SqlAlchemyBillingRepository` and `InMemoryBillingRepository` MUST implement it.

#### Scenario: Period has Invoices
- GIVEN Invoices exist for a `period_id`
- WHEN `get_by_period_id(period_id)` is called
- THEN the system returns matching Invoices

#### Scenario: Period has no Invoices
- GIVEN no Invoices for a `period_id`
- WHEN `get_by_period_id(period_id)` is called
- THEN the system returns an empty list
