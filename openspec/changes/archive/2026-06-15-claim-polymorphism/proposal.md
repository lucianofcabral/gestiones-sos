# Proposal: Claim Polymorphism

## Intent

Today all claims are implicitly SOS — the model, forms, list, and detail view hardcode SosClaim everywhere. This blocks adding new claim types (batch lots, invoices, ad-hoc) without coupling. We need a discriminator-driven model where `ClaimKind` determines behavior at every layer.

## Scope

### In Scope
- Discriminator column on `Claim` via `ClaimKind` (values: sos, tres_arroyos, adhoc, grouped)
- `GroupedClaim` entity: batch lots with FK to repurposed `GroupClaim`, no individual `gestion`
- `GroupClaim` repurposed: from simple lookup to batch entity (`external_reference` required, `description` optional)
- Form dispatch at `/gestiones/nueva`: render SOS or Grouped sections per selected kind
- List adapt at `/gestiones`: type-discriminated columns, type column added
- Detail adapt at `/gestiones/{id}`: render type-specific sections

### Out of Scope
- Document association (deferred)
- Ad-hoc / Tres Arroyos-specific forms (ClaimKind values exist but no form yet)
- Group claim CRUD UI updates (existing CRUD works with new fields)

## Capabilities

### New Capabilities
- `claim-types`: Polymorphic Claim model with `ClaimKind` discriminator. Defines the dispatch contract — every claim type has a registration use case, a DTO, and a detail serializer.

### Modified Capabilities
- `claim-registration`: Form renders dynamically per selected `ClaimKind`. SOS card shows existing fields; Grouped batch card replaces `gestion` with `group_claim_id + notes`.
- `claim-listing`: `ObtenerGestiones` returns all types. New `type` column. SOS rows show `gestion`; Grouped rows show `external_reference`. Delete dispatch per type.
- `claim-detail`: `ObtenerGestionPorId` returns type-discriminated sections. SOS history table vs. Grouped batch info card.

## Approach

1. **Add discriminator**: `Claim.claim_kind_id` already exists (FK to `ClaimKind`). Use it as the discriminator — no schema change needed on `Claim`.
2. **New entity**: `GroupedClaim` table (claim_id FK, group_claim_id FK, notes). No `gestion`.
3. **Repurpose GroupClaim**: Add `external_reference` (required), `description` (optional), keep `group_id` as PK. Migrate existing rows: `external_reference = name`.
4. **Repository**: New `GroupedClaimRepoPort`. Extend `ClaimRepoPort.get_all()` to include kind filter.
5. **Use cases**: `RegistrarGroupedClaim` (new), `RegistrarGestionSOS` unchanged. `ObtenerGestiones` adapted for type dispatch.
6. **UI dispatch**: Form checks `ClaimKind` on selection → renders relevant sections. List/detail reads kind → renders type-specific columns/cards.

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `domain/entities/` | Modified | `Claim` uses discriminator; `GroupClaim` gets new fields |
| `domain/entities/` | New | `GroupedClaim` entity |
| `domain/ports/` | New | `GroupedClaimRepoPort` |
| `domain/use_cases/` | New | `RegistrarGroupedClaim` |
| `domain/use_cases/` | Modified | `ObtenerGestiones`, `ObtenerGestionPorId` — type dispatch |
| `infra/repositories/` | New | `GroupedClaimRepoImpl` |
| `infra/repositories/` | Modified | `GroupClaimRepoImpl` — new fields |
| `presentation/gestiones_nueva.py` | Modified | Dynamic form per claim type |
| `presentation/gestiones_lista.py` | Modified | Type-aware columns |
| `presentation/gestiones_detalle.py` | Modified | Type-aware sections |
| `openspec/specs/group-claim/spec.md` | Modified | New purpose: batch entity |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Existing GroupClaim rows have no `external_reference` | High | Migration script sets `external_reference = name` |
| SosClaim form breaks if discriminator is wrong | Low | Client-side validation enforces kind selection before render |
| GroupedClaim without `gestion` breaks list view sort | Medium | Sort by `created_at` fallback when `gestion` is null |

## Rollback Plan

Revert the schema migration for `GroupedClaim` + `GroupClaim` new columns. Restore `ObtenerGestiones` to the pre-polymorphic join. The `ClaimKind` discriminator column already exists and is safe to keep.

## Dependencies

- Database migration for `GroupClaim` new columns + `GroupedClaim` table
- Existing `ClaimKind` seed data must include "grouped" (editable catalog)

## Success Criteria

- [ ] Agent creates an SOS claim — workflow unchanged
- [ ] Agent creates a Grouped batch claim — no `gestion`, linked to a batch
- [ ] List view shows both types with correct columns per type
- [ ] Detail view renders SOS history OR Grouped batch info per claim type
- [ ] All existing tests pass without modification
