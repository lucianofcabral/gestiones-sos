# Archive Report: claim-polymorphism

**Archived**: 2026-06-15
**Archive path**: `openspec/changes/archive/2026-06-15-claim-polymorphism/`

## Executive Summary

Claim polymorphism introduces a discriminator-driven claim model where `ClaimKind` determines behavior at every layer — registration, listing, detail, and deletion. The existing `Claim.claim_kind_id` FK serves as the discriminator (zero schema change on `claims`). A new `GroupedClaim` entity supports batch lots linked to a repurposed `GroupClaim` (now with `external_reference` and `description`). The UI dynamically adapts form sections, list columns, and detail cards per claim type.

The change was delivered across 4 chained PRs, totaling 18 tasks, 64+ new tests, and full spec compliance (24/25 scenarios compliant; 1 partial for sort fallback).

## What Was Delivered

| Capability | Description | Status |
|------------|-------------|--------|
| Polymorphic Claim Model | `Claim.claim_kind_id` discriminator; `GroupedClaim` entity; `GroupClaim` batch fields | ✅ Delivered |
| Dynamic Registration Form | Type selector → conditional SOS/Grouped cards with type-dispatched use cases | ✅ Delivered |
| Type-Aware Listing | "Tipo" column; type-dispatch for gestion/reference and delete | ✅ Delivered |
| Type-Aware Detail | Type badge in header; conditional Section 2 (SOS Records vs Grouped Data card) | ✅ Delivered |
| Extensibility Contract | New claim types require only: seed value, FK table, use case, DTO, serializer | ✅ Delivered |

## Files Changed / Created

### Domain Layer (4 files)
| File | Action |
|------|--------|
| `src/domain/models/entities.py` | Modified — `GroupClaim` gains `external_reference`, `description`; new `GroupedClaim` entity |
| `src/domain/ports/repositories.py` | Modified — new `GroupedClaimRepoPort` protocol |
| `src/domain/ports/uow.py` | Modified — `grouped_claims: GroupedClaimRepoPort` added |

### Infrastructure / Persistence (5 files)
| File | Action |
|------|--------|
| `src/infrastructure/database/tables.py` | Modified — `group_claims` columns; new `grouped_claims` table |
| `src/adapters/persistence/sqlalchemy_grouped_claim_repository.py` | **Created** — `GroupedClaimRepoPort` implementation |
| `src/adapters/persistence/sqlalchemy_group_claim_repository.py` | Modified — updated for new fields |
| `src/adapters/persistence/sqlalchemy_unit_of_work.py` | Modified — wire `grouped_claims` repo |
| Alembic migration script | **Created** — ALTER + backfill + CREATE TABLE |

### Use Cases (5 files)
| File | Action |
|------|--------|
| `src/application/use_cases/claims/registrar_grouped_claim.py` | **Created** |
| `src/application/use_cases/claims/eliminar_grouped_claim.py` | **Created** |
| `src/application/use_cases/claims/obtener_gestiones.py` | Modified — type-aware join |
| `src/application/use_cases/claims/obtener_gestion_por_id.py` | Modified — type dispatch |
| `src/infrastructure/container.py` | Modified — wiring |

### UI Layer (3 files)
| File | Action |
|------|--------|
| `src/ui/pages/gestiones_nueva.py` | Modified — type selector + conditional cards |
| `src/ui/pages/gestiones.py` | Modified — "Tipo" column + type-dispatch delete |
| `src/ui/pages/gestiones_detalle.py` | Modified — conditional Section 2 |

### Tests (4 files, 64+ new tests)
| File | Action |
|------|--------|
| `tests/test_claims.py` | Modified — RegistrarGroupedClaim + EliminarGroupedClaim tests |
| `tests/test_claims_detail.py` | Modified — type dispatch for detail |
| `tests/test_claims_integration.py` | **Created** — CRUD + backfill |
| `tests/test_claims_ui_dispatch.py` | **Created** — kind classification + dispatch |

## Spec Delta Status

| Domain | Action | Details |
|--------|--------|---------|
| `claim-types` | **Created** | New main spec — polymorphic model, discriminator, extensibility contract |
| `claim-registration` | **Updated** | 3 ADDED requirements (type selector, conditional forms, batch dropdown); 3 MODIFIED (registration, validation, duplicate gestion); 1 REMOVED (original form layout) |
| `claim-listing` | **Updated** | 1 ADDED (type column); 3 MODIFIED (listar, delete, sort fallback) |
| `claim-detail` | **Updated** | 1 ADDED (grouped batch card); 2 MODIFIED (obtener por id, UI sections) |
| `group-claim` | **Updated** | 1 ADDED (batch entity requirement); 1 MODIFIED (create with new fields) |

## Verification Results

- **Tasks**: 18/18 complete (100%)
- **Tests**: 381 passed (0 failures, including 64+ claim-polymorphism tests)
- **Lint**: ✅ Passed (ruff)
- **Spec compliance**: 24/25 scenarios compliant (1 partial — sort fallback UI gap)
- **Verdict**: **PASS WITH WARNINGS** — 1 minor UI gap (no sort mechanism for gestion/reference column)
- **Critical issues**: 0

## Known Limitations / Future Work

| Item | Impact | Suggested Timing |
|------|--------|-----------------|
| Sort fallback for Grouped rows | Sort by `created_at` when `gestion` is null is NOT implemented in UI — DTO provides data but no sort mechanism exists | v2.1 |
| Column header "Gestión/Ref." | Shows both gestion and reference but may not be intuitive | v2.1 (UX review) |
| Ad-hoc / Tres Arroyos forms | `ClaimKind` values exist but no form implementation | v3.0 |
| Document association | Deferred from scope — no document gallery integration for claims | v3.0 |
| GroupClaim CRUD UI | Existing CRUD works with new fields but no dedicated batch management UI | v2.2 |
| ObtenerGestiones filter by kind | Currently returns all types — filtering scope is future need | v2.1 |
| List join performance | In-memory join works at current scale; may need DB join at scale | When performance degrades |

## Rollback Instructions

1. **Schema rollback**: Reverse the Alembic migration — `DROP TABLE grouped_claims`; `ALTER TABLE group_claims DROP COLUMN external_reference, DROP COLUMN description`
2. **Code rollback**: Revert changed files to prior commit (pre-claim-polymorphism)
3. **Data preservation**: `Claim.claim_kind_id` already existed before this change — safe to keep.
4. **Configuration**: No config changes were needed

## SDD Cycle Complete

The claim-polymorphism change has been fully planned, implemented, verified, and archived. All delta specs have been merged into baseline main specs. The archived change folder serves as the audit trail.
