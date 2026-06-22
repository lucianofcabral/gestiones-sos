# Proposal: nueva-gestion — New Claim Form

## Intent

Agents need a form at `/gestiones/nueva` to register SOS claims. Currently the route is a placeholder. The use case (`RegistrarGestionSOS`) and UOW already exist and are tested — the gap is the UI, wire-up, and the `ObtenerClaimKinds` dropdown use case.

## Scope

### In Scope
- Form UI with two sections: Claim data + SOS data
- Dropdown for **claim_kind** (via new `ObtenerClaimKinds` use case)
- Dropdown for **group** (via existing `ObtenerGrupos`)
- Status dropdown with 3 options: `CERRADO`, `ABIERTO`, `RECHAZADO`
- Wire `RegistrarGestionSOS` in container (first UOW use case)
- Create `ObtenerClaimKinds` use case following `ObtenerGrupos` pattern
- Validation: required fields, duplicate gestion guard, error display via `ui.notify`
- Success: notify + redirect to `/gestiones`

### Out of Scope
- Auto-generation of gestion number (manual entry)
- Document upload during registration
- Inline editing or multi-step wizard
- Advanced field rules (e.g., conditional visibility)

## Capabilities

### New Capabilities
- `claim-registration`: Form at `/gestiones/nueva` to create Claim + SosClaim atomically.

### Modified Capabilities
- `claim-listing`: Updated success flow — after registration, redirect to `/gestiones`.

## Approach

1. **`ObtenerClaimKinds`** — new use case in `src/application/use_cases/claims/`, repo-only, same pattern as `ObtenerGrupos`.
2. **Container wiring** — add `ObtenerClaimKinds` and `RegistrarGestionSOS` instances. For UOW, create a fresh `SqlAlchemyUnitOfWork()` per use-case access (UOW creates its connection lazily in `__enter__`). The container property returns a new `RegistrarGestionSOS(SqlAlchemyUnitOfWork())` each call.
3. **Form page** — replace `gestiones_nueva.py` placeholder. Two-section card layout using NiceGUI components. Load dropdown options on page init. On submit: validate, call use case, notify, redirect.

### Form Fields Layout

**Claim Data** (card): claim_kind (dropdown), group (dropdown), claimer_name (text), policy_number (text), plate (text), claimed_amount (number), comment (textarea).

**SOS Data** (card): gestion (number, required — duplicate guard exists), category (text), reason (text), load_user (text), response_user (text), status (dropdown: CERRADO/ABIERTO/RECHAZADO), itr (number).

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `src/application/use_cases/claims/obtener_claim_kinds.py` | New | ObtenerClaimKinds use case |
| `src/infrastructure/container.py` | Modified | Wire ObtenerClaimKinds + RegistrarGestionSOS |
| `src/ui/pages/gestiones_nueva.py` | Modified | Replace placeholder with form |
| `openspec/specs/claim-registration/spec.md` | New | Capability spec |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| UOW wiring in container (new pattern) | Medium | Each access creates fresh `SqlAlchemyUnitOfWork` — UOW is lightweight |
| Dropdown data loading blocks page render | Low | Sync load on page init; data is small (claim kinds, groups) |

## Rollback Plan

Revert `gestiones_nueva.py` to placeholder, remove new use case file from imports/wiring, delete `claim-registration` spec.

## Dependencies

- `RegistrarGestionSOS` use case (exists, tested)
- `SqlAlchemyUnitOfWork` (exists)
- `ObtenerGrupos` (exists, wired)

## Success Criteria

- [ ] Agent fills all fields, submits — claim + sos claim created, redirect to `/gestiones`
- [ ] Duplicate gestion number shows error toast, no DB change
- [ ] Missing required fields blocked before submit
- [ ] `ObtenerClaimKinds` returns all claim kinds from DB
- [ ] All 3 existing use case tests still pass
