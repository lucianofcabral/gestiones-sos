# Tasks: Domain Exceptions

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | ~130–180 |
| 400-line budget risk | Low |
| Chained PRs recommended | No |
| Suggested split | Single PR |
| Delivery strategy | single-pr-default |
| Chain strategy | pending |

Decision needed before apply: No
Chained PRs recommended: No
Chain strategy: pending
400-line budget risk: Low

## Phase 1: Foundation

- [x] 1.1 Create `src/domain/exceptions.py` — `DomainError(Exception)` base class + all 12 concrete exceptions (`ClaimNotFoundError`, `ClaimHasActivePaymentsError`, `GestionAlreadyExistsError`, `PeriodRequiredError`, `AgentNotConfiguredError`, `InvalidNCConfigurationError`, `InvalidPaymentUpdateError`, `InvalidCredentialsError`, `UserInactiveError`, `EmailAlreadyRegisteredError`, `UserNotFoundError`, `InvalidTokenError`)

## Phase 2: Claims — Replace ValueError

- [x] 2.1 `src/application/use_cases/claims/eliminar_gestion_sos.py` — import typed exceptions, replace 2 `raise ValueError(...)` with `raise ClaimNotFoundError(...)` and `ClaimHasActivePaymentsError(...)`
- [x] 2.2 `src/application/use_cases/claims/registrar_gestion_sos.py` — import, replace 1 raise with `GestionAlreadyExistsError`
- [x] 2.3 `tests/test_claims.py` — update 2 `pytest.raises(ValueError, ...)` assertions to corresponding typed exceptions

## Phase 3: Payments — Replace ValueError

- [x] 3.1 `src/application/use_cases/payments/registrar_pago.py` — import, replace 4 raises with `PeriodRequiredError`, `AgentNotConfiguredError`, `InvalidNCConfigurationError` (x2)
- [x] 3.2 `src/domain/services/payment_update_rules.py` — import, replace 2 raises with `InvalidPaymentUpdateError`
- [x] 3.3 `tests/test_payments.py` — update 5 `pytest.raises(ValueError, ...)` to typed exceptions (actual count)

## Phase 4: Auth — Replace ValueError

- [x] 4.1 `src/application/use_cases/auth/use_cases.py` — import, replace 5 raises with `InvalidCredentialsError` (x2), `UserInactiveError`, `EmailAlreadyRegisteredError`, `UserNotFoundError`
- [x] 4.2 `src/ui/routes/auth.py` — import, replace 1 raise with `InvalidTokenError`
- [x] 4.3 `tests/test_auth.py` — update 3 `pytest.raises(ValueError, ...)` to typed exceptions

## Phase 5: Verification

- [x] 5.1 Grep `src/application/ src/domain/ src/ui/` — confirm zero business `raise ValueError` remains
- [x] 5.2 Run full test suite — all tests pass with typed exception assertions
