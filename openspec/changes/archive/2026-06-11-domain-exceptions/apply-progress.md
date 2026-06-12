# Apply Progress: Domain Exceptions

## Summary
Implemented all 12 tasks. Created typed domain exceptions and replaced all bare `raise ValueError(...)` business-error statements across the codebase.

## Key Design Decision
`DomainError` inherits from `ValueError` (not `Exception`) so that existing `except ValueError` catch blocks in `src/ui/routes/auth.py` continue to work without modification.

## TDD Cycle Evidence
| Task | Test File | Layer | Safety Net | RED | GREEN | TRIANGULATE | REFACTOR |
|------|-----------|-------|------------|-----|-------|-------------|----------|
| 1.1 | N/A (structural) | N/A | ✅ 140/140 | N/A (structural) | ✅ Created | ➖ Skipped (structural) | ✅ Clean |
| 2.1 | test_claims.py | Unit | ✅ 140/140 | ✅ Updated test assertions | ✅ 6/6 passed | ➖ Refactor only | ✅ Clean |
| 2.2 | test_claims.py | Unit | ✅ 140/140 | ✅ Updated test assertions | ✅ 6/6 passed | ➖ Refactor only | ✅ Clean |
| 2.3 | test_claims.py | Unit | ✅ 140/140 | ✅ ClaimNotFoundError, GestionAlreadyExistsError | ✅ 6/6 passed | ➖ Refactor only | ✅ Clean |
| 3.1 | test_payments.py | Unit | ✅ 140/140 | ✅ Updated test assertions | ✅ 39/39 passed | ➖ Refactor only | ✅ Clean |
| 3.2 | test_payments.py | Unit | ✅ 140/140 | ✅ Updated test assertions | ✅ 39/39 passed | ➖ Refactor only | ✅ Clean |
| 3.3 | test_payments.py | Unit | ✅ 140/140 | ✅ 5 asserts to typed exceptions | ✅ 39/39 passed | ➖ Refactor only | ✅ Clean |
| 4.1 | test_auth.py | Unit | ✅ 140/140 | ✅ Updated test assertions | ✅ 8/8 passed | ➖ Refactor only | ✅ Clean |
| 4.2 | test_auth.py | Unit | ✅ 140/140 | ✅ Updated test assertions | ✅ 8/8 passed | ➖ Refactor only | ✅ Clean |
| 4.3 | test_auth.py | Unit | ✅ 140/140 | ✅ 3 asserts to typed exceptions | ✅ 8/8 passed | ➖ Refactor only | ✅ Clean |
| 5.1 | N/A | N/A | N/A | N/A | ✅ Zero remaining | N/A | N/A |
| 5.2 | all | Full suite | N/A | N/A | ✅ 140/140 passed | N/A | N/A |

## Files Changed
| File | Action | What Was Done |
|------|--------|---------------|
| `src/domain/exceptions.py` | Created | 12 typed exception classes + DomainError base |
| `src/application/use_cases/claims/eliminar_gestion_sos.py` | Modified | Import + 2 raises replaced |
| `src/application/use_cases/claims/registrar_gestion_sos.py` | Modified | Import + 1 raise replaced |
| `src/application/use_cases/payments/registrar_pago.py` | Modified | Import + 4 raises replaced |
| `src/domain/services/payment_update_rules.py` | Modified | Import + 2 raises replaced |
| `src/application/use_cases/auth/use_cases.py` | Modified | Import + 5 raises replaced |
| `src/ui/routes/auth.py` | Modified | Import + 1 raise replaced |
| `tests/test_claims.py` | Modified | 2 ValueError assertions → typed exceptions |
| `tests/test_payments.py` | Modified | 5 ValueError assertions → typed exceptions |
| `tests/test_auth.py` | Modified | 3 ValueError assertions → typed exceptions |
| `openspec/changes/domain-exceptions/tasks.md` | Modified | All tasks marked [x] |

## Deviations from Design
None — implementation matches the proposal.

## Test Summary
- Baseline: 140 tests passing
- After implementation: 140 tests passing
- `ruff check`: 0 new issues (4 pre-existing warnings unaffected)
