# Payment CRUD Specification

## Purpose

Full CRUD lifecycle for Payment entities — create, query, update, soft-delete (inactivate/activate), and inactivation eligibility check.

## Requirements

### Requirement: Create Payment

The system MUST create a Payment with fields: payment_id, claim_id, payer_id, payment_via_id, payee_id, amount, created_date, active (default True).

When `payment_via_id` resolves to name "Nota de Crédito" via PaymentViaRepoPort, the system MUST validate that `payer_id` resolves to agent name "SOS" and `payee_id` resolves to agent name "SM" via AgentRepoPort. On validation failure, the system MUST raise `ValueError`.

#### Scenario: Happy path — transferencia payment
- GIVEN valid claim_id, payer_id, payee_id, payment_via_id (transferencia), and amount
- WHEN the use case executes
- THEN the system creates the Payment with `active=True` and returns it

#### Scenario: Nota de Crédito with wrong payer
- GIVEN `payment_via_id` resolves to "Nota de Crédito"
- WHEN `payer_id` does NOT resolve to agent "SOS"
- THEN the system raises `ValueError`

#### Scenario: Nota de Crédito with wrong payee
- GIVEN `payment_via_id` resolves to "Nota de Crédito"
- WHEN `payee_id` does NOT resolve to agent "SM"
- THEN the system raises `ValueError`

### Requirement: Get Payment by ID

The system MUST return a Payment by `payment_id`, or `None` if not found.

#### Scenario: Payment exists
- GIVEN a Payment exists in the store
- WHEN the use case executes with its `payment_id`
- THEN the system returns the matching Payment

#### Scenario: Payment not found
- GIVEN no Payment exists for the given `payment_id`
- WHEN the use case executes
- THEN the system returns `None`

### Requirement: List All Payments

The system MUST return all Payments (active and inactive).

#### Scenario: Multiple payments exist
- GIVEN several Payments in the store
- WHEN the use case executes
- THEN the system returns the full list

### Requirement: Update Payment

The system MUST update non-identity fields (not `payment_id`, `claim_id`) by `payment_id`. Returns `True` on success, `False` if not found.

#### Scenario: Update amount and payee
- GIVEN a Payment exists
- WHEN the use case executes with new `amount` and `payee_id`
- THEN the system updates those fields and returns `True`

#### Scenario: Update non-existent payment
- GIVEN no Payment for the given `payment_id`
- WHEN the use case executes
- THEN the system returns `False`

### Requirement: Inactivate Payment

The system MUST set `active=False` on a Payment by `payment_id`. Returns `True` on success, `False` if not found.

#### Scenario: Inactivate existing payment
- GIVEN a Payment with `active=True`
- WHEN the use case executes
- THEN the system sets `active=False` and returns `True`

#### Scenario: Inactivate non-existent payment
- GIVEN no Payment for the given `payment_id`
- WHEN the use case executes
- THEN the system returns `False`

### Requirement: Activate Payment

The system MUST set `active=True` on a Payment by `payment_id`. Returns `True` on success, `False` if not found.

#### Scenario: Activate existing payment
- GIVEN a Payment with `active=False`
- WHEN the use case executes
- THEN the system sets `active=True` and returns `True`

### Requirement: Check Inactivatable

The system MUST return whether a Payment has no NcPayment references, making it safe to inactivate.

#### Scenario: No NcPayment exists
- GIVEN no NcPayment references this `payment_id`
- WHEN `inactivatable(payment_id)` is called
- THEN the system returns `True`

#### Scenario: NcPayment exists
- GIVEN an NcPayment references this `payment_id`
- WHEN `inactivatable(payment_id)` is called
- THEN the system returns `False`

### Requirement: Get Payments by Claim ID

The system MUST return all Payments (active and inactive) that reference a given `claim_id`.

#### Scenario: Payments exist for claim

- GIVEN one or more Payments reference a `claim_id`
- WHEN `get_by_claim_id(claim_id)` is called
- THEN the system returns the matching Payments

#### Scenario: No payments for claim

- GIVEN no Payments reference the given `claim_id`
- WHEN `get_by_claim_id(claim_id)` is called
- THEN the system returns an empty list
