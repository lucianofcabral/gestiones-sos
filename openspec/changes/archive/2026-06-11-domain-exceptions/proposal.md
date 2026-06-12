# Proposal: Domain Exceptions

## Intent

Replace all bare `raise ValueError(...)` business-error statements across the
codebase with typed domain exception classes. Currently every domain violation
— claim not found, invalid credentials, duplicate gestion, payment misconfig —
is indistinguishable at the type level. This makes error handling fragile,
testing ambiguous, and the API surface unclear.

## Scope

### In Scope
- Define `DomainError` base class and concrete exception types in
  `src/domain/exceptions.py`
- Replace `raise ValueError(...)` in domain services, use cases, and auth routes
- Update tests from `pytest.raises(ValueError)` to the matching typed exception
- Keep existing error messages intact as exception arguments

### Out of Scope
- HTTP error mapping (4xx/5xx from exceptions) — deferred
- Logging or error-reporting middleware changes
- Non-business `ValueError` usage (e.g. parsing, validation in pure infrastructure)

## Capabilities

### New Capabilities
- None — pure refactor, no spec-level behavior changes.

### Modified Capabilities
- None — no existing capability changes at the spec level.

## Approach

1. **Base class**: `class DomainError(Exception)` — simple marker, no extra logic.
2. **Concrete types** (all in `src/domain/exceptions.py`):

   | Exception | Replaces | Source |
   |-----------|----------|--------|
   | `ClaimNotFoundError` | `ValueError("Claim not found")` | `eliminar_gestion_sos.py` |
   | `ClaimHasActivePaymentsError` | `ValueError("Claim has active payments")` | `eliminar_gestion_sos.py` |
   | `GestionAlreadyExistsError` | `ValueError("Ya existe...")` | `registrar_gestion_sos.py` |
   | `PeriodRequiredError` | `ValueError("period_id is required...")` | `registrar_pago.py` |
   | `AgentNotConfiguredError` | `ValueError("SOS or SM agent...")` | `registrar_pago.py` |
   | `InvalidNCConfigurationError` | `ValueError("NC payment must have SOS...")` x2 | `registrar_pago.py` |
   | `InvalidPaymentUpdateError` | `ValueError("Only amount..."/"Cannot change...")` | `payment_update_rules.py` |
   | `InvalidCredentialsError` | `ValueError("Invalid credentials")` x2 | `auth/use_cases.py` |
   | `UserInactiveError` | `ValueError("User is inactive")` | `auth/use_cases.py` |
   | `EmailAlreadyRegisteredError` | `ValueError("Email already registered")` | `auth/use_cases.py` |
   | `UserNotFoundError` | `ValueError("User not found")` | `auth/use_cases.py` |
   | `InvalidTokenError` | `ValueError("Invalid token")` | `ui/routes/auth.py` |

3. **Replace & import**: one commit per domain (auth, claims, payments) for
   reviewability.
4. **Update tests**: `pytest.raises(ValueError)` → `pytest.raises(ClaimNotFoundError)`,
   import from `src.domain.exceptions`.

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `src/domain/exceptions.py` | **New** | 12 exception classes |
| `src/application/use_cases/claims/eliminar_gestion_sos.py` | Modified | 2 raises replaced |
| `src/application/use_cases/claims/registrar_gestion_sos.py` | Modified | 1 raise replaced |
| `src/application/use_cases/payments/registrar_pago.py` | Modified | 4 raises replaced |
| `src/domain/services/payment_update_rules.py` | Modified | 2 raises replaced |
| `src/application/use_cases/auth/use_cases.py` | Modified | 5 raises replaced |
| `src/ui/routes/auth.py` | Modified | 1 raise replaced |
| `tests/test_claims.py` | Modified | 4 assertions updated |
| `tests/test_payments.py` | Modified | 6 assertions updated |
| `tests/test_auth.py` | Modified | 3 assertions updated |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Missed `raise ValueError(...)` | Low | grep for all instances after replacement |
| Test breaks from import errors | Low | Run test suite after each commit |

## Rollback Plan

Revert the commit(s). Each domain is a separate commit — partial rollback is
safe. No DB migration, no data risk, no config change.

## Dependencies

None — all changes are self-contained within the Python source tree.

## Success Criteria

- [ ] `src/domain/exceptions.py` is populated with typed exceptions
- [ ] Zero `raise ValueError(...)` business-error statements remain in domain
      services, use cases, or auth routes
- [ ] All tests pass with typed exception assertions
- [ ] No spec-level behavior changes (all existing scenarios still pass)
