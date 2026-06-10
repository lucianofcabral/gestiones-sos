# Tasks: Payment CRUD — Update & Activate

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | ~350 |
| 400-line budget risk | Low |
| Chained PRs recommended | No |
| Suggested split | Single PR |
| Delivery strategy | ask-always |

Decision needed before apply: Yes
Chained PRs recommended: No
Chain strategy: pending
400-line budget risk: Low

### Suggested Work Units

| Unit | Goal | Likely PR | Notes |
|------|------|-----------|-------|
| 1 | Domain services + entity + use cases + container + tests | PR 1 | Single PR, all changes additive |

## Phase 1: Domain Layer — Foundation

- [x] 1.1 Modify `Payment.amount` from `ge=0` to `gt=0` in `src/domain/models/entities.py`
- [x] 1.2 Create `src/domain/services/payment_update_rules.py` with `PaymentUpdateRules` (depends on `NcPaymentRepoPort`, `PaymentViaRepoPort`; `validate()` raises `ValueError` on rule violations)
- [x] 1.3 Create `src/domain/services/can_activate_payment.py` with `CanActivatePaymentService` (depends on `ClaimRepoPort`; `execute(payment)` returns `tuple[bool, str]`)

## Phase 2: Application Layer — Use Cases

- [x] 2.1 Create `src/application/use_cases/payments/actualizar_pago.py` with `ActualizarPagoInput`, `ActualizarPagoOutput`, `ActualizarPago.execute()` — delegates to `PaymentUpdateRules.validate()`, then `PaymentRepoPort.update()`
- [x] 2.2 Create `src/application/use_cases/payments/activar_pago.py` with `ActivarPagoInput`, `ActivarPagoOutput`, `ActivarPago.execute()` — delegates to `CanActivatePaymentService.execute()`, then `PaymentRepoPort.activate()`

## Phase 3: Infrastructure — Wiring

- [x] 3.1 Wire domain services `PaymentUpdateRules` and `CanActivatePaymentService` in `src/infrastructure/container.py`
- [x] 3.2 Wire use cases `ActualizarPago` and `ActivarPago` in `src/infrastructure/container.py`

## Phase 4: Testing

- [x] 4.1 Add test: `Payment(amount=0)` raises Pydantic `ValidationError`
- [x] 4.2 Add fixture + test: `PaymentUpdateRules` rejects change to NC via when no NC exists → `ValueError`
- [x] 4.3 Test: `PaymentUpdateRules` rejects non-amount field when NC exists → `ValueError`
- [x] 4.4 Test: `PaymentUpdateRules` allows amount-only change when NC exists → no error
- [x] 4.5 Test: `CanActivatePaymentService` returns `(True, ...)` when claim is active
- [x] 4.6 Test: `CanActivatePaymentService` returns `(False, ...)` when claim is inactive
- [x] 4.7 Test: `ActualizarPago` happy path → `success=True`, repo updated
- [x] 4.8 Test: `ActualizarPago` not found → `success=False`
- [x] 4.9 Test: `ActivarPago` happy path → `success=True`, payment activated
- [x] 4.10 Test: `ActivarPago` not found → `success=False`
