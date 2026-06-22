# Design: Claim Polymorphism

## Technical Approach

Discriminator-driven dispatch using the existing `Claim.claim_kind_id` FK. Type-specific data lives in dedicated tables (`sos_claims`, `grouped_claims`) — the discriminator determines which table to join at each layer (repo → use case → UI). `GroupClaim` gains `external_reference` and `description` to function as a batch entity. No changes to the `Claim` base schema.

## Architecture Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Discriminator | Existing `Claim.claim_kind_id` | Already exists and seeded — zero schema change on `claims` |
| Type data model | Separate FK tables per type | Referential integrity, no nullable bloat |
| List join | In-memory in `ObtenerGestiones` | Matches existing pattern, acceptable at current scale |
| Detail dispatch | Type-check on `claim_kind_id` | Simple for 2 types; extract strategy pattern later |
| Delete dispatch | Per-type use cases | Existing `EliminarGestionSOS` untouched, no regression risk |
| UI conditionals | NiceGUI `bind_visibility` | Already available, avoids full reload |
| UoW connection | Pass `conn=` to repos | Existing proven pattern, single transaction |

## Data Flow

```
Registration: Type selector → kind dispatch (SOS→RegistrarGestionSOS, Grouped→RegistrarGroupedClaim)

Listing:  claim_repo.get_all() → join in-memory with sos_claims or grouped_claims → GroupClaim.external_reference

Detail:   claim_repo.get_by_id(id) → kind dispatch → type-specific fetch + payments always
```

## Data Model

```python
class GroupClaim(BaseModel):
    group_id: UUID = Field(default_factory=uuid4)
    name: str = Field(min_length=1, max_length=100)
    external_reference: str = Field(min_length=1, max_length=100)   # NEW, required, unique
    description: str | None = None                                   # NEW, optional
    created_at: datetime = Field(default_factory=datetime.now)

class GroupedClaim(BaseModel):                                       # NEW
    grouped_claim_id: UUID = Field(default_factory=uuid4)
    claim_id: UUID = Field(default_factory=uuid4)
    group_claim_id: UUID = Field(default_factory=uuid4)
    notes: str = Field("", max_length=500)
    created_at: datetime = Field(default_factory=datetime.now)
```

## File Changes

| File | Action | Description |
|------|--------|-------------|
| `src/domain/models/entities.py` | Modify | `GroupClaim`: add `external_reference`, `description`. New `GroupedClaim` entity |
| `src/domain/ports/repositories.py` | Modify | New `GroupedClaimRepoPort` protocol |
| `src/domain/ports/uow.py` | Modify | Add `grouped_claims: GroupedClaimRepoPort` |
| `src/infrastructure/database/tables.py` | Modify | `group_claims`: add `external_reference` (varchar, not null, unique), `description` (varchar, nullable). New `grouped_claims` table |
| `src/adapters/persistence/sqlalchemy_group_claim_repository.py` | Modify | Update `add`/`update`/`_row_to_entity` for new fields |
| `src/adapters/persistence/sqlalchemy_grouped_claim_repository.py` | **Create** | Implements `GroupedClaimRepoPort` |
| `src/adapters/persistence/sqlalchemy_unit_of_work.py` | Modify | Wire `grouped_claims` repo in `__enter__` |
| `src/application/use_cases/claims/registrar_grouped_claim.py` | **Create** | Creates Claim + GroupedClaim atomically via UoW |
| `src/application/use_cases/claims/eliminar_grouped_claim.py` | **Create** | Soft-deletes GroupedClaim + Claim |
| `src/application/use_cases/claims/obtener_gestiones.py` | Modify | Add `GroupedClaimRepoPort`, `GroupClaimRepoPort` deps. Type-aware join. New DTO fields |
| `src/application/use_cases/claims/obtener_gestion_por_id.py` | Modify | Type-dispatch for detail: fetch SosClaim records OR GroupedClaim + GroupClaim batch |
| `src/ui/pages/gestiones_nueva.py` | Modify | Type selector dropdown + conditional SOS/Grouped card rendering |
| `src/ui/pages/gestiones.py` | Modify | "Tipo" column, type-dispatch for gestion/reference and delete |
| `src/ui/pages/gestiones_detalle.py` | Modify | Conditional Section 2: SOS Records table or Grouped Data card |
| `src/infrastructure/container.py` | Modify | Wire new repos, use cases, and update `ObtenerGestiones`/`ObtenerGestionPorId` |
| Migration script | **Create** | ALTER `group_claims` ADD columns; CREATE `grouped_claims`; UPDATE `external_reference = name` |

## Interfaces / Contracts

```python
class GroupedClaimRepoPort(BaseRepo[GroupedClaim], Protocol):
    def get_by_claim_id(self, claim_id: UUID) -> GroupedClaim | None: ...

class UnitOfWork(ABC):
    claims: ClaimRepoPort
    sos_claims: SosClaimRepoPort
    grouped_claims: GroupedClaimRepoPort   # NEW
```

### DTO changes

```
GestionDTO:
  + claim_kind_name: str          # "SOS", "Grouped", etc.
  - gestion: int                  # replaced by:
  + gestion_or_reference: str     # "12345" or "Lote-2024-001"

GestionDetalleDTO:
  + grouped_data: GroupedClaimDetailDTO | None = None
  # sos_records unchanged — empty list when type is grouped
```

## Testing Strategy

| Layer | What to Test | Approach |
|-------|-------------|----------|
| Unit | `GroupedClaim` entity validation | Pydantic field tests |
| Unit | `RegistrarGroupedClaim` | Mock `UnitOfWork`, verify atomic create |
| Unit | `ObtenerGestiones` type dispatch | Mock repos, assert correct DTO per type |
| Unit | `ObtenerGestionPorId` type dispatch | Mock repos, assert `grouped_data` vs `sos_records` |
| Integration | Repository CRUD (`GroupedClaimRepoPort`) | Real DB with test fixture |
| Integration | Migration backfill | Run migration on test DB, verify `external_reference = name` |

## Migration / Rollout

1. Migration #1: ALTER `group_claims` — add `external_reference` (nullable initially), `description`
2. Migration #2: UPDATE `group_claims SET external_reference = name` (backfill)
3. Migration #3: ALTER `group_claims` — set `external_reference` NOT NULL + UNIQUE
4. Migration #4: CREATE TABLE `grouped_claims`
5. Deploy code and migrations together. Rollback: reverse migrations + revert code changes.

## Open Questions

- [ ] Does the "Gestión N°" column header change to something generic or stay as-is (since it shows external_reference for grouped rows)?
- [ ] Should `ObtenerGestiones` support filtering by `claim_kind_id` (future need) or keep as "all types"?
