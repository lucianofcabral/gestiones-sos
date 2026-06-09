# Tasks: UI App Shell

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | ~530 |
| 400-line budget risk | Medium |
| Chained PRs recommended | No |
| Suggested split | Single PR |
| Delivery strategy | auto-forecast |
| Chain strategy | size-exception |

Decision needed before apply: No
Chained PRs recommended: No
Chain strategy: size-exception
400-line budget risk: Medium

### Suggested Work Units

| Unit | Goal | Likely PR | Notes |
|------|------|-----------|-------|
| 1 | AppShell + placeholder pages + home + main refactor | Single PR | Under 800-line budget; all parts are tightly coupled (each page depends on AppShell) |

## Phase 1: Foundation — AppShell Component

- [x] 1.1 Create `src/ui/components/shell.py` — `AppShell` context manager with `__enter__` (auth guard via `app.storage.user["token"]`, `ui.dark_mode().enable()`, `ui.header()`, `ui.left_drawer()` sidebar), `_render_header()`, `_render_sidebar()`, `_nav_item()` helper, and `__exit__`
- [x] 1.2 Create `src/ui/pages/gestiones.py` — placeholder at `/gestiones` with `with AppShell():` + title label
- [x] 1.3 Create `src/ui/pages/gestiones_nueva.py` — placeholder at `/gestiones/nueva`
- [x] 1.4 Create `src/ui/pages/gestiones_detalle.py` — placeholder at `/gestiones/{id}` (dynamic route)
- [x] 1.5 Create `src/ui/pages/pagos.py` — placeholder at `/pagos`
- [x] 1.6 Create `src/ui/pages/periodos.py` — placeholder at `/periodos`
- [x] 1.7 Create `src/ui/pages/reportes.py` — placeholder at `/reportes`

## Phase 2: Home Page Rewrite

- [x] 2.1 Rewrite `src/ui/pages/home.py` — wrap in `with AppShell():`, replace module cards with metrics dashboard: total claims counter, recent 5 claims table (claimer, policy, plate, date), stat cards (pending SOS, active payments, current period), empty states for zero-data scenarios
- [x] 2.2 Deprecate `src/ui/components/navbar.py` — add deprecation docstring; remove `crear_navbar()` usage from home.py

## Phase 3: Integration — main.py

- [x] 3.1 Refactor `main.py` — import and call all 7 page registrations, remove old `navbar`/`register_home_page` imports, add CSS overrides for dark theme (`ui.add_head_html` for light-class neutralization)

## Phase 4: Testing

- [x] 4.1 Test `shell.py` — mock `app.storage.user`, assert redirect when token missing, assert dark mode enabled, assert sidebar nav items rendered, assert header shows user name
- [x] 4.2 Test `home.py` — seed `InMemoryClaimRepository` via Container, verify metrics and stat cards render with data; verify empty states render without crash
- [x] 4.3 Test placeholder pages — navigate to each route, assert 200 + AppShell chrome renders
