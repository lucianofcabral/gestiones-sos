# Tasks: Claim Polymorphism

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | 650–850 |
| 400-line budget risk | High |
| Chained PRs recommended | Yes |
| Suggested split | PR #1 (Foundation) → PR #2 (Use Cases) → PR #3 (UI + Wiring) → PR #4 (Tests) |
| Delivery strategy | force-chained |
| Chain strategy | stacked-to-main |

Decision needed before apply: Yes
Chained PRs recommended: Yes
Chain strategy: stacked-to-main
400-line budget risk: High

### Suggested Work Units

| Unit | Goal | Likely PR | Notes |
|------|------|-----------|-------|
| 1 | Domain + persistence foundation | PR #1 | Additive — no behavioral changes, merges to main |
| 2 | New & refactored use cases | PR #2 | Depends on PR #1 for repo protocol and entity |
| 3 | UI dispatch + container wiring | PR #3 | Depends on PR #2 for use cases |
| 4 | Tests for all layers | PR #4 | Depends on PR #3 for final code |

## Phase 1: Domain & Data (Foundation)

- [x] 1.1 Migration script: ALTER `group_claims` ADD `external_reference` (nullable), `description`; backfill `external_reference = name`; set NOT NULL + UNIQUE; CREATE TABLE `grouped_claims`
- [x] 1.2 `src/domain/models/entities.py` — add `external_reference`, `description` to `GroupClaim`; add `GroupedClaim` entity
- [x] 1.3 `src/domain/ports/repositories.py` — add `GroupedClaimRepoPort` protocol with `get_by_claim_id`
- [x] 1.4 `src/domain/ports/uow.py` — add `grouped_claims: GroupedClaimRepoPort` to `UnitOfWork`
- [x] 1.5 `src/infrastructure/database/tables.py` — add columns to `group_claims`; new `grouped_claims` table

## Phase 2: Persistence (Repositories)

- [x] 2.1 **Create** `src/adapters/persistence/sqlalchemy_grouped_claim_repository.py` — implement `GroupedClaimRepoPort` with SQLAlchemy Core
- [x] 2.2 `src/adapters/persistence/sqlalchemy_group_claim_repository.py` — update `add`, `update`, `_row_to_entity` for new fields
- [x] 2.3 `src/adapters/persistence/sqlalchemy_unit_of_work.py` — wire `grouped_claims` repo in `__enter__`

## Phase 3: Use Cases

- [x] 3.1 **Create** `src/application/use_cases/claims/registrar_grouped_claim.py` — `RegistrarGroupedClaim` (Claim + GroupedClaim atomically via UoW)
- [x] 3.2 **Create** `src/application/use_cases/claims/eliminar_grouped_claim.py` — `EliminarGroupedClaim` (soft-delete Claim, guard: active payments)
- [x] 3.3 `src/application/use_cases/claims/obtener_gestiones.py` — add `GroupedClaimRepoPort` + `GroupClaimRepoPort` deps; type-aware in-memory join; new `GestionDTO` fields: `claim_kind_name`, `gestion_or_reference`
- [x] 3.4 `src/application/use_cases/claims/obtener_gestion_por_id.py` — type-dispatch detail: fetch `SosClaim` records OR `GroupedClaim` + `GroupClaim` batch per `claim_kind_id`; add `GroupedClaimDetailDTO`; guard: `GroupedClaim` not found raises `ClaimNotFoundError`

## Phase 4: UI

- [x] 4.1 `src/ui/pages/gestiones_nueva.py` — type selector dropdown at top; conditional "Claim Data" + "SOS Data" / "Grouped Data" card rendering; type-dispatch submit to `RegistrarGestionSOS` or `RegistrarGroupedClaim`
- [x] 4.2 `src/ui/pages/gestiones.py` — add "Tipo" first column; type-dispatch `gestion_or_reference` display; type-dispatch delete to `EliminarGestionSOS` or `EliminarGroupedClaim`
- [x] 4.3 `src/ui/pages/gestiones_detalle.py` — conditional Section 2: SOS Records table for `sos` / Grouped Data card for `grouped`; show `gestion` or `external_reference` in header; type badge

## Phase 5: Wiring

- [x] 5.1 `src/infrastructure/container.py` — wire `SqlAlchemyGroupedClaimRepository`; register `RegistrarGroupedClaim`, `EliminarGroupedClaim`; update `ObtenerGestiones` and `ObtenerGestionPorId` with new deps

## Phase 6: Tests

- [x] 6.1 Unit: `GroupedClaim` entity validation; `RegistrarGroupedClaim` with mocked UoW; `EliminarGroupedClaim` with payment guard
- [x] 6.2 Unit: `ObtenerGestiones` type dispatch — assert `gestion_or_reference` from `SosClaim.gestion` vs `GroupClaim.external_reference`
- [x] 6.3 Unit: `ObtenerGestionPorId` type dispatch — assert `grouped_data` vs `sos_records` and `ClaimNotFoundError` for missing claim
- [x] 6.4 Integration: `SqlAlchemyGroupedClaimRepository` CRUD with real DB fixture (truth tables: `claims`, `group_claims`, `grouped_claims`)
- [x] 6.5 Integration: migration backfill — verify `external_reference = name` for all existing rows
- [x] 6.6 UI: type selector renders, conditional form visibility, type-dispatch submit and delete flows (page-level assertions)
