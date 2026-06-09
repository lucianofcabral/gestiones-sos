# Proposal: UI App Shell & Layout

## Intent

Replace ad-hoc page structure (blue headers, no sidebar) with a cohesive dark-themed App Shell providing sidebar navigation, route protection, and consistent layout foundation for all upcoming pages.

## Scope

### In Scope
- Dark theme via `ui.dark_mode().enable()` — no toggle
- App Shell: sidebar (expandable), top header, main content area
- Route protection: redirect unauthenticated → `/login`
- Home page with real metrics + recent claims for insurance operators
- Placeholder pages for all planned screens
- `main.py` refactor to centralize page registration

### Out of Scope
- Theme switcher, mobile layout, user profile, notifications, real-time updates

## Capabilities

### New
- `ui-app-shell`: Dark-themed layout with sidebar, route protection, consistent chrome

### Modified
- None — first UI capability, no existing specs

## Approach

`AppShell` context manager wrapping each page. On entry:
1. Check auth (`app.storage.user["token"]`) → redirect `/login`
2. Enable `ui.dark_mode()`
3. Render sidebar (`ui.left_drawer`) + header (`ui.header()`)
4. Yield content area for the page

**New files:**
- `src/ui/components/shell.py` — `AppShell` class
- `src/ui/pages/gestiones.py`, `gestiones_nueva.py`, `gestiones_detalle.py`
- `src/ui/pages/pagos.py`, `periodos.py`, `reportes.py`

**Modified files:**
- `src/ui/pages/home.py` — metrics + recent 5 claims
- `src/ui/components/navbar.py` — simplify or remove
- `main.py` — register new pages, mount App Shell

**Home content:** total claims counter, recent 5 claims (claimer, policy, plate, date), stat cards (pending SOS, active payments, current period). Empty states handled.

## Affected Areas

| Area | Impact |
|------|--------|
| `src/ui/components/shell.py` | New |
| `src/ui/pages/home.py` | Modified |
| `src/ui/pages/*.py` (6 files) | New |
| `src/ui/components/navbar.py` | Modified |
| `main.py` | Modified |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| `left_drawer` breaks on nav | Medium | Test each page; fallback `ui.row()` sidebar |
| Dark theme clashes with page styles | Low | Override light-bg assumptions |
| Sidebar state not persisted | Low | Accept default; persist in `app.storage` later |

## Rollback Plan

`git revert` the commit, or restore `main.py` to old registration, remove shell, disable dark mode.

## Dependencies

- Container (`claim_repo`, `payment_repo`, `period_repo`) for metrics
- Existing `app.storage.user["token"]` auth pattern
- NiceGUI: `ui.left_drawer`, `ui.header`, `ui.dark_mode`

## Success Criteria

- [ ] All pages render correctly with dark theme
- [ ] Unauthenticated users redirected to `/login`
- [ ] Sidebar navigation works on all routes
- [ ] Home metrics render on empty and populated DB
- [ ] Placeholder pages render without errors
- [ ] `ruff check .` passes
