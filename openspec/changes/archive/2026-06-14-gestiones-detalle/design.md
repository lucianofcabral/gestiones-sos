# Design: Gestiones Detalle

## Technical Approach

Add an `ObtenerGestionPorId` use case that fetches a single Claim by ID, joins all related SosClaim records, group/kind names, and payments, then returns a structured `GestionDetalleDTO`. Rewrite the placeholder page at `/gestiones/{id}` with three sections: claim header, SOS records table, payments table. Wire the use case in the Container and add row-click navigation from the list page.

Follows the exact pattern established by `ObtenerGestiones`/`GestionDTO` — input DTO, pydantic output models, repo-ports-only constructor, Container property exposure.

## Architecture Decisions

### Decision: Use Input DTO for consistency

| Option | Tradeoff |
|--------|----------|
| Plain `claim_id: UUID` arg | Fewer files, but breaks from `EliminarGestionSOSInput` pattern |
| `ObtenerGestionPorIdInput` with `claim_id` field | Consistent with existing use cases; trivial overhead |

**Choice**: `ObtenerGestionPorIdInput(claim_id: UUID)` — consistency over brevity.

### Decision: Return `GestionDetalleDTO` directly (no output wrapper)

| Option | Tradeoff |
|--------|----------|
| `ObtenerGestionPorIdOutput(detalle=...)` | Consistent with `ObtenerGestionesOutput` but adds pointless nesting for a single return |
| Return `GestionDetalleDTO` | Simpler; `ObtenerGestionesOutput` exists only because it wraps a list |

**Choice**: Return `GestionDetalleDTO` directly — the output DTO *is* the detail.

### Decision: GroupClaimRepoPort.get_by_claim_id returns `GroupClaim`, not Optional

The port signature is `get_by_claim_id(claim_id: UUID) -> GroupClaim` (not `| None`), but the in-memory impl returns `None` when unmatched. The use case will handle this gracefully — if `None`, set `group_name` to empty string. The implementation will type the variable as `GroupClaim | None` and the runtime handles it.

## Data Flow

```
Page /gestiones/{id}
  │
  ▼
container.obtener_gestion_por_id.execute(ObtenerGestionPorIdInput(claim_id))
  │
  ├─ claim_repo.get_by_id(claim_id) ──────────→ Claim | None
  │     └─ None → raise ClaimNotFoundError
  │
  ├─ sos_claim_repo.get_claims_by_claim_id(claim_id) ──→ list[SosClaim]
  ├─ group_claim_repo.get_by_claim_id(claim_id) ───────→ GroupClaim (or None at runtime)
  ├─ claim_kind_repo.get_by_id(claim.claim_kind_id) ───→ ClaimKind | None
  ├─ payment_repo.get_by_claim_id(claim_id) ───────────→ list[Payment]
  │
  └─ assemble GestionDetalleDTO ──────────────────→ return

Page renders:
  ┌─ Back button → /gestiones
  ├─ Section 1: Claim header card (number, asegurado, póliza, patente, monto)
  ├─ Section 2: SOS records table (gestion, category, reason, status, users, itr)
  └─ Section 3: Payments table (amount, dates, active)
```

## File Changes

| File | Action | Description |
|------|--------|-------------|
| `src/application/use_cases/claims/obtener_gestion_por_id.py` | **Create** | New use case + DTOs |
| `src/ui/pages/gestiones_detalle.py` | **Modify** | Rewrite placeholder → 3-section detail view |
| `src/ui/pages/gestiones.py` | **Modify** | Add `on_click` row navigation to `/gestiones/{id}` |
| `src/infrastructure/container.py` | **Modify** | Wire `_obtener_gestion_por_id` use case |
| `src/application/use_cases/claims/__init__.py` | **Modify** | No-op (already empty; imports are direct) |
| `tests/test_claims_detail.py` | **Create** | Unit tests for new use case |

## Interfaces / Contracts

```python
# --- Input / Output DTOs ---

class ObtenerGestionPorIdInput(BaseModel):
    claim_id: UUID


class SosClaimDetailDTO(BaseModel):
    sos_claim_id: UUID
    gestion: int
    category: str
    reason: str
    status: str
    load_user: str
    response_user: str
    itr: int


class PaymentDTO(BaseModel):
    payment_id: UUID
    amount: float
    created_date: datetime
    active: bool


class GestionDetalleDTO(BaseModel):
    # Claim fields
    claim_id: UUID
    claimer_name: str
    policy_number: str
    plate: str
    claimed_amount: float
    comment: str
    solved: bool
    active: bool
    created_at: datetime
    # Joined data
    group_name: str
    claim_kind_name: str
    # Children
    sos_records: list[SosClaimDetailDTO]
    payments: list[PaymentDTO]


# --- Use case ---

class ObtenerGestionPorId:
    def __init__(
        self,
        claim_repo: ClaimRepoPort,
        sos_claim_repo: SosClaimRepoPort,
        group_claim_repo: GroupClaimRepoPort,
        claim_kind_repo: ClaimKindRepoPort,
        payment_repo: PaymentRepoPort,
    ) -> None: ...

    def execute(self, input_data: ObtenerGestionPorIdInput) -> GestionDetalleDTO:
        # 1. claim_repo.get_by_id → None → raise ClaimNotFoundError
        # 2. sos_claim_repo.get_claims_by_claim_id
        # 3. group_claim_repo.get_by_claim_id → extract name (or "")
        # 4. claim_kind_repo.get_by_id(claim.claim_kind_id) → extract name (or "")
        # 5. payment_repo.get_by_claim_id
        # 6. Assemble and return GestionDetalleDTO
        ...
```

## Testing Strategy

| Layer | What | Approach |
|-------|------|----------|
| Unit | `ObtenerGestionPorId` — happy path | Seed all 5 in-memory repos, verify DTO fields |
| Unit | Claim not found | Empty claim repo → assert `ClaimNotFoundError` |
| Unit | No SosClaims | Seed claim only → empty `sos_records` list |
| Unit | No payments | Seed claim only → empty `payments` list |
| Unit | Group/kind name fallback | Missing group/kind → empty string in DTO |

Follows existing `test_claims_list.py` pattern: `InMemory*Repository` fixtures, `_seed_*` helpers.

## Migration / Rollout

No migration required. The placeholder page is replaced atomically; in-flight navigations will 404 naturally if the route is down during deploy.

## Open Questions

- [ ] `GroupClaimRepoPort.get_by_claim_id` returns `GroupClaim` (not `| None`) in the Protocol but the in-memory impl returns `None`. Should the Protocol signature be corrected? — Currently handled at the use case level with a runtime guard.
