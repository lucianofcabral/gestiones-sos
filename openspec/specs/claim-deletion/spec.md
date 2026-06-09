# Claim Deletion Specification

## Purpose

Soft-delete (inactivate) a Claim with a payment guard — the system MUST prevent deletion when the Claim has active Payments referencing it.

## Requirements

### Requirement: Payment Guard on Claim Deletion

The `EliminarGestionSOS` use case MUST accept a `PaymentRepoPort` parameter alongside its existing `ClaimRepoPort`. Before inactivating the Claim, it MUST check for active Payments referencing the Claim via `payment_repo.get_by_claim_id(claim_id)`. If any returned Payment has `active=True`, the system MUST raise `ValueError("Claim has active payments")`.

The existing behavior (Claim not found → ValueError, inactive claim → idempotent success) MUST remain unchanged. The payment guard check MUST happen AFTER the "Claim not found" check and BEFORE `inactivate()`.

#### Scenario: Claim with active payments — deletion blocked

- GIVEN a Claim exists with `active=True`
- AND one or more Payments reference that claim with `active=True`
- WHEN `EliminarGestionSOS.execute()` is called
- THEN the system raises `ValueError("Claim has active payments")`
- AND the Claim remains `active=True`

#### Scenario: Claim with only inactive payments — deletion allowed

- GIVEN a Claim exists with `active=True`
- AND one or more Payments reference that claim, all with `active=False`
- WHEN `EliminarGestionSOS.execute()` is called
- THEN the system sets `claim.active=False`
- AND returns `success=True`

#### Scenario: Claim without payments — deletion allowed (unchanged)

- GIVEN a Claim exists with `active=True`
- AND no Payments reference that claim
- WHEN `EliminarGestionSOS.execute()` is called
- THEN the system sets `claim.active=False`
- AND returns `success=True`

#### Scenario: Claim not found — unchanged behavior

- GIVEN no Claim exists for the given `claim_id`
- WHEN `EliminarGestionSOS.execute()` is called
- THEN the system raises `ValueError("Claim not found")`
