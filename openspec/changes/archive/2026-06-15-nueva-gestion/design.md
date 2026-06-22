# Design: nueva-gestion — New Claim Form

## Technical Approach

Two-phase client-rendered form at `/gestiones/nueva` using NiceGUI. Phase 1 (page load): fetch groups and claim kinds from the existing `ObtenerGrupos` use case and a new `ObtenerClaimKinds` use case. Phase 2 (submit): validate client-side, then call `RegistrarGestionSOS` via the container. Success notifies and redirects to `/gestiones`. Duplicate gestion numbers are caught server-side by the use case and surfaced via `ui.notify`.

The UOW-based use case (`RegistrarGestionSOS`) is the first use case in this project that requires a `UnitOfWork`, not a repo. The container wires it by creating a fresh `SqlAlchemyUnitOfWork()` per property access — the UOW is stateless until `__enter__` opens a connection, so there is no lifecycle issue.

## Architecture Decisions

### Decision: UOW wiring strategy

| Option | Tradeoff | Decision |
|--------|----------|----------|
| A: Factory lambda in container | More ceremony, unused complexity | ❌ |
| B: Property creates new `SqlAlchemyUnitOfWork()` each call | Simple, matches Singleton pattern, UOW is lazy | ✅ |

**Rationale**: `SqlAlchemyUnitOfWork.__init__` does nothing — the connection opens in `__enter__`. Creating a fresh instance per property access is safe, zero-cost, and follows the existing container pattern (repos are singletons because they hold no state; UOW is the first stateless-session pattern).

### Decision: ObtenerClaimKinds mirrors ObtenerGrupos

**Choice**: `ObtenerClaimKinds(repo: ClaimKindRepoPort)` with `execute() -> list[ClaimKind]`, identical to the ObtenerGrupos pattern.
**Alternatives**: Add a `buscar_por_texto` method like ObtenerGrupos has — rejected as out of scope for this form.
**Rationale**: The claim-kinds list is small (3-10 entries), full fetch is fine. Search is not needed.

### Decision: Form sections as independent cards

**Choice**: Two `ui.card()` components inside `AppShell`, one per data section.
**Rationale**: Matches the existing card-based layout in `gestiones_detalle.py`. Clear visual separation between Claim-level data and SOS-specific data.

### Decision: Status as tri-state select

**Choice**: `ui.select` with options `["ABIERTO", "CERRADO", "RECHAZADO"]`, no default selection.
**Rationale**: Forces explicit choice. These match the domain values stored in `SosClaim.status`.

## Data Flow

```
Page: /gestiones/nueva

on_page_load:
  Container.get_instance()
    → container.obtener_grupos.execute()     → list[GroupClaim]
    → container.obtener_claim_kinds.execute() → list[ClaimKind]
    → Populate ui.select dropdowns

on_submit:
  Validate required fields (client-side)
    ↓ invalid → ui.notify("Campo requerido", type="warning")
    ↓ valid
  Build RegistrarGestionSOSInput
  container.registrar_gestion_sos.execute(input)
    ↓ GestionAlreadyExistsError → ui.notify(..., type="negative")
    ↓ success
  ui.notify("Gestión registrada", type="positive")
  ui.navigate.to("/gestiones")
```

## File Changes

| File | Action | Description |
|------|--------|-------------|
| `src/application/use_cases/claims/obtener_claim_kinds.py` | Create | New use case: `ObtenerClaimKinds(repo)`, `execute() -> list[ClaimKind]` |
| `src/infrastructure/container.py` | Modify | Add imports + properties for `ObtenerClaimKinds`, `RegistrarGestionSOS` |
| `src/ui/pages/gestiones_nueva.py` | Modify | Replace placeholder with 2-card form |
| `tests/test_claim_kinds.py` | Create | Tests for ObtenerClaimKinds (mirror test_grupos.py pattern) |

### ObtenerClaimKinds — Full Module

```python
"""ObtenerClaimKinds — list all claim kinds."""

from src.domain.models.entities import ClaimKind
from src.domain.ports.repositories import ClaimKindRepoPort


class ObtenerClaimKinds:
    """Return all ClaimKinds (ordered by name)."""

    def __init__(self, repo: ClaimKindRepoPort) -> None:
        self._repo = repo

    def execute(self) -> list[ClaimKind]:
        return self._repo.get_all()
```

### Container Changes

New imports (insert alphabetically near line 56):
```python
from src.application.use_cases.claims.obtener_claim_kinds import ObtenerClaimKinds
from src.application.use_cases.claims.registrar_gestion_sos import RegistrarGestionSOS
from src.adapters.persistence.sqlalchemy_unit_of_work import SqlAlchemyUnitOfWork
```

New constructor init (after `self._obtener_grupos` line ~209):
```python
# Claim registration use cases
self._obtener_claim_kinds = ObtenerClaimKinds(self._claim_kind_repo)
self._registrar_gestion_sos = RegistrarGestionSOS(SqlAlchemyUnitOfWork())
```

New properties:
```python
@property
def obtener_claim_kinds(self) -> ObtenerClaimKinds:
    return self._obtener_claim_kinds

@property
def registrar_gestion_sos(self) -> RegistrarGestionSOS:
    return self._registrar_gestion_sos
```

### Form UI — Component Tree

```
AppShell
├── ui.label("Nueva Gestión")
├── ui.card ("Datos del Reclamo")
│   ├── ui.select("Tipo de Reclamo", options=[... from claim_kinds])
│   ├── ui.select("Grupo", options=[... from groups])
│   ├── ui.input("Asegurado")
│   ├── ui.input("Póliza")
│   ├── ui.input("Patente")
│   ├── ui.number("Monto Reclamado")
│   └── ui.textarea("Comentario")
├── ui.card ("Datos SOS")
│   ├── ui.number("Gestión N°")
│   ├── ui.input("Categoría")
│   ├── ui.input("Motivo")
│   ├── ui.input("Usuario Carga")
│   ├── ui.input("Usuario Respuesta")
│   ├── ui.select("Estado", options=["ABIERTO", "CERRADO", "RECHAZADO"])
│   └── ui.number("ITR")
└── ui.button("Registrar Gestión")
```

### Validation Rules

| Field | Rule | Message |
|-------|------|---------|
| claim_kind_id | Required (must select) | "Debe seleccionar un tipo de reclamo" |
| group_id | Required (must select) | "Debe seleccionar un grupo" |
| claimer_name | Required, non-empty | "El nombre del asegurado es requerido" |
| policy_number | Required, non-empty | "El número de póliza es requerido" |
| plate | Required, min 6 chars | "La patente es requerida" |
| gestion | Required, > 0 | "El número de gestión es requerido" |
| status | Required (must select) | "Debe seleccionar un estado" |

## Interfaces / Contracts

No new ports or repository protocols. `ObtenerClaimKinds` reuses the existing `ClaimKindRepoPort` interface.

## Testing Strategy

| Layer | What to Test | Approach |
|-------|-------------|----------|
| Unit | `ObtenerClaimKinds.execute()` with populated / empty repo | InMemoryClaimKindRepository, mirror TestObtenerGrupos |
| Integration | Container wiring — both new use cases resolve | Existing test infrastructure |
| Integration | RegistrarGestionSOS with real UOW | Existing test_claims.py (no change needed) |

## Migration / Rollout

No migration required. The form is behind a route that was previously a placeholder — deploying adds the feature with zero data impact.

## Open Questions

None.
