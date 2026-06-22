# Design: Gestiones Listado

## Technical Approach

Create a new `ObtenerGestiones` use case that fetches all Claims and SosClaims from their respective repos, joins them in-memory by `claim_id`, and returns a combined DTO. Wire `sos_claim_repo` as a Container property (it's currently absent). Replace the `/gestiones` placeholder page with a `@ui.refreshable` table following the `facturacion.py` pattern.

## Architecture Decisions

### Decision: SosClaimRepoPort must be a Container property

| Option | Tradeoff | Decision |
|--------|----------|----------|
| Wire `sos_claim_repo` as Container property | ~10 lines; follows all existing repo patterns (e.g. `_build_billing_repo`) | **Chosen** |
| Pass `ObtenerGestiones` a `UnitOfWork` | Overkill for a read-only query; UoW implies transactional intent | Rejected |
| Inject `SqlAlchemySosClaimRepository` directly at use-case level | Leaks infrastructure into application layer | Rejected |

**Rationale**: Every other repo in the codebase has a `_build_*` factory + Container property. SosClaimRepoPort is the only one missing it. Adding it is consistent, minimal, and unblocks the use case without architectural debt.

### Decision: ObtenerGestiones under claims use cases directory

**Choice**: `src/application/use_cases/claims/obtener_gestiones.py`
**Rationale**: Colocated with `eliminar_gestion_sos.py` and `registrar_gestion_sos.py`. The `obtener_facturas.py` pattern lives under `billing/` — same logic for claims.

### Decision: In-memory join, no repo changes

**Rationale**: Both repos already expose `get_all()`. The data volume is small (<10k records). No new repo methods needed. The join is a simple dict lookup: `{s.claim_id: s for s in sos_claims}`.

## Data Flow

```
/gestiones page load
  │
  ├─→ container.obtener_gestiones.execute(include_inactive=False)
  │     │
  │     ├─→ claim_repo.get_all()  ──→ list[Claim]
  │     ├─→ sos_claim_repo.get_all() ──→ list[SosClaim]
  │     │
  │     └─→ Join: dict {claim_id → SosClaim}
  │         → Filter: active=True (unless include_inactive)
  │         → Map to list[GestionDTO]
  │         → Return ObtenerGestionesOutput
  │
  └─→ Render table with columns

Delete action
  ├─→ Confirmation dialog (ui.dialog)
  └─→ container.eliminar_gestion_sos.execute(EliminarGestionSOSInput)
      → On success: _render_gestiones.refresh()
      → On error: ui.notify(type="negative")
```

## File Changes

| File | Action | Description |
|------|--------|-------------|
| `src/application/use_cases/claims/obtener_gestiones.py` | **Create** | `ObtenerGestiones` + `ObtenerGestionesOutput` + `GestionDTO` |
| `src/infrastructure/container.py` | **Modify** | Add `_sos_claim_repo` (factory + property), wire `ObtenerGestiones` |
| `src/ui/pages/gestiones.py` | **Modify** | Replace placeholder with `@ui.refreshable` table, toggle, delete dialog |

## Interfaces / Contracts

```python
# src/application/use_cases/claims/obtener_gestiones.py

class GestionDTO(BaseModel):
    claim_id: UUID
    gestion: int
    claimer_name: str
    policy_number: str
    plate: str
    claimed_amount: float
    category: str
    reason: str
    status: str
    load_user: str
    response_user: str
    itr: int
    solved: bool
    active: bool
    created_at: datetime

class ObtenerGestionesOutput(BaseModel):
    gestiones: list[GestionDTO]

class ObtenerGestiones:
    def __init__(self, claim_repo: ClaimRepoPort, sos_claim_repo: SosClaimRepoPort) -> None: ...
    def execute(self, include_inactive: bool = False) -> ObtenerGestionesOutput: ...
```

### Container wiring

```python
# New factory
def _build_sos_claim_repo() -> SosClaimRepoPort:
    if not os.environ.get("DATABASE_URL"):
        raise RuntimeError("DATABASE_URL environment variable is not set")
    return SqlAlchemySosClaimRepository()

# In Container.__init__:
self._sos_claim_repo = _build_sos_claim_repo()
self._obtener_gestiones = ObtenerGestiones(self._claim_repo, self._sos_claim_repo)

# Property:
@property
def obtener_gestiones(self) -> ObtenerGestiones:
    return self._obtener_gestiones
```

### Use case implementation

```
execute(include_inactive=False):
  1. claims = self._claim_repo.get_all()
  2. sos_claims_map = {s.claim_id: s for s in self._sos_claim_repo.get_all()}
  3. For each claim:
     a. sc = sos_claims_map.get(claim.claim_id)
     b. Skip if not include_inactive and not claim.active
     c. Build GestionDTO(claim + sc fields)
  4. Return ObtenerGestionesOutput(gestiones=...)
```

## Testing Strategy

| Layer | What to Test | Approach |
|-------|-------------|----------|
| Unit | `ObtenerGestiones.execute(include_inactive=False)` | Seed `InMemoryClaimRepository` + `InMemorySosClaimRepository`, verify DTO count and field mapping |
| Unit | `ObtenerGestiones.execute(include_inactive=True)` | Same fixtures, verify inactive claims included |
| Unit | Empty repos → empty list | Verify `gestiones == []` |
| Unit | Field mapping correctness | Assert every `GestionDTO` field matches source, including missing SosClaim (defaults) |
| E2E | Table renders correctly | Manual — start app, navigate to `/gestiones` |

## Migration / Rollout

No migration required. The `sos_claim_repo` property is additive — no existing code is affected.

## Open Questions

None.
