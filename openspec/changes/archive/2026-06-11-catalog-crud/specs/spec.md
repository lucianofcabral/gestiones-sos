# Delta Specs: catalog-crud

## Assessment

After reviewing the proposal (`openspec/changes/catalog-crud/proposal.md`) and existing specs (`openspec/specs/navigation/spec.md`, `openspec/specs/catalog-listing/` — not found):

### Proposed Capabilities

| Capability | Type | Classification | Rationale |
|-----------|------|---------------|-----------|
| `catalog-listing` | New | **Infrastructure-only** | Read-only table UI (`ui.table` + `ui.tabs`) with no business behavior, no validation, no transformation. Direct repo reads with no use case layer. Purely enabling plumbing for existing specs (payment-crud, claim-deletion). |
| `navigation` | Modified | **Infrastructure-only** | Adding a single sidebar link (`/catalogos`) is a UI navigation concern with zero behavioral contract change. The existing navigation spec covers the sidebar rendering mechanism, not the link inventory. |

### Existing Specs Check

- `openspec/specs/navigation/spec.md` — Unchanged. The sidebar rendering, header, and page registration requirements remain valid. Adding a link is implementation, not a spec delta.
- `openspec/specs/catalog-listing/spec.md` — Does not exist. Would be a new spec, but this change's scope is read-only infrastructure plumbing, not a user-facing capability requiring spec'd behavior.

## Conclusion

**No delta specs.** All proposed work is infrastructure/plumbing — enabling existing specs (payment-crud, claim-deletion) to resolve real data from SQLAlchemy repos instead of stub `None` values. No behavioral contracts are added, modified, or removed.

The 3 new tables (agents, payment_vias, claim_kinds), 3 repos, 3 in-memory stores, Alembic migration, and read-only `/catalogos` page are implementation details for existing payment/claim validation behavior.
