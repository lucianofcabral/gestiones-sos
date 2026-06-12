# Archive Report: domain-exceptions

**Archived at**: 2026-06-11
**Type**: Pure refactor — no spec-level behavior changes
**Artifact mode**: both (openspec files + Engram)

## Change Summary

Replaced all bare `raise ValueError(...)` business-error statements across the codebase with 12 typed domain exception classes. No spec-level behavior changes — this is a pure refactor that improves type safety, test precision, and domain clarity without altering any capability.

### Key Design Decision

`DomainError` inherits from `ValueError` (not `Exception`) — a deliberate deviation from the original proposal for backward compatibility with existing `except ValueError` catch blocks in `src/ui/routes/auth.py`.

## Verification Verdict

**PASS with warnings** (design deviation documented and accepted)

| Metric | Value |
|--------|-------|
| Tasks | 12/12 complete |
| Tests | 140/140 passed |
| Lint regressions | 0 new issues (3 pre-existing) |
| Remaining `raise ValueError` | 0 in business logic |
| Build | N/A (no build step) |

## Artifact Traceability

### Openspec Files (in archive path)

| Artifact | Path |
|----------|------|
| Proposal | `openspec/changes/archive/2026-06-11-domain-exceptions/proposal.md` |
| Tasks | `openspec/changes/archive/2026-06-11-domain-exceptions/tasks.md` |
| Apply Progress | `openspec/changes/archive/2026-06-11-domain-exceptions/apply-progress.md` |
| Verify Report | `openspec/changes/archive/2026-06-11-domain-exceptions/verify-report.md` |
| Archive Report | `openspec/changes/archive/2026-06-11-domain-exceptions/archive-report.md` |

### Engram Artifacts

| Artifact | Topic Key | Type |
|----------|-----------|------|
| Proposal | `sdd/domain-exceptions/proposal` | `architecture` |
| Tasks | `sdd/domain-exceptions/tasks` | `architecture` |
| Verify Report | `sdd/domain-exceptions/verify-report` | `architecture` |
| Archive Report | `sdd/domain-exceptions/archive-report` | `architecture` |

## Specs Synced

**None** — this change has no delta specs (`openspec/changes/domain-exceptions/specs/` never existed). The proposal served as the specification since there are no new capabilities or behavior changes.

## SDD Cycle Complete

This change has been fully proposed, implemented, verified, and archived. The cycle is closed.

### Files Changed (for reference)

| File | Action |
|------|--------|
| `src/domain/exceptions.py` | Created (62 lines, 12 exceptions + DomainError base) |
| `src/application/use_cases/claims/eliminar_gestion_sos.py` | Modified (2 raises replaced) |
| `src/application/use_cases/claims/registrar_gestion_sos.py` | Modified (1 raise replaced) |
| `src/application/use_cases/payments/registrar_pago.py` | Modified (4 raises replaced) |
| `src/domain/services/payment_update_rules.py` | Modified (2 raises replaced) |
| `src/application/use_cases/auth/use_cases.py` | Modified (5 raises replaced) |
| `src/ui/routes/auth.py` | Modified (1 raise replaced) |
| `tests/test_claims.py` | Modified (2 assertions updated) |
| `tests/test_payments.py` | Modified (5 assertions updated) |
| `tests/test_auth.py` | Modified (3 assertions updated) |
