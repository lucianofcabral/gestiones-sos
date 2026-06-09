# Design: UI App Shell

## Technical Approach

Replace ad-hoc per-page auth + navbar with an `AppShell` context manager that
wraps every authenticated page. On entry: redirect unauthenticated → `/login`,
enable dark theme, render sidebar + header, then yield the content area for the
page to fill. Auth pages (login, register) bypass AppShell entirely.

## Architecture Decisions

### Decision: Context manager over base class or decorator

| Option | Tradeoff |
|--------|-|
| Base class `AppPage(ui.page)` | Tight coupling to NiceGUI internals; inheritance hierarchy |
| Decorator `@with_shell` | NiceGUI's `@ui.page` already registers routes — stacking decorators hides flow |
| **Context manager** `with AppShell():` | Clear scope, explicit entry/exit, composable with any `@ui.page` function |

**Choice**: Context manager. Matches NiceGUI's own `with ui.column():` pattern.

### Decision: `ui.left_drawer` as sidebar

| Option | Tradeoff |
|--------|-|
| **`ui.left_drawer`** | NiceGUI native, collapse built-in, responsive |
| Custom `ui.column()` | Works everywhere but no native collapse/overlay |

**Choice**: `ui.left_drawer`. Fallback to `ui.row().classes("w-48")` only if
drawer fails to render (capture in try/except at construction).

### Decision: Repo calls directly from page vs use case wrappers

| Option | Tradeoff |
|--------|-|
| **Direct repo calls** | Home page is a read-only dashboard; no business logic to encapsulate |
| New use cases | Adds ceremony for what is essentially a query |

**Choice**: Direct repo calls via Container for home metrics. Use cases are
for commands with business rules, not reads.

## Data Flow

```
User hits "/"
  → @ui.page("/") home_page()
  → with AppShell()
      → check app.storage.user["token"] — redirect /login if missing
      → ui.dark_mode().enable()
      → render header + sidebar
      → yield content area
  → [page code runs inside content area]
  → [on exit] implicit context cleanup
```

```
Home metrics flow:

home_page() → Container.get_instance()
  ├── claim_repo.get_all()          → total count + recent 5 (sorted by created_at desc)
  ├── claim_repo.get_all()          → filter active SOS claims for "pending SOS" count
  ├── payment_repo.get_all()        → filter active payments
  └── period_repo.get_n_last(1)     → current period

All data rendered inline with .set_text() or ui.row() bindings.
```

## Component Tree

```
ui.page("/...")
  └── AppShell (context manager)
      ├── ui.dark_mode().enable()          # set once on first entry
      ├── ui.header()
      │   ├── ui.icon("local_police")
      │   ├── ui.label("Gestiones SOS")
      │   ├── user_name label
      │   └── logout button
      ├── ui.left_drawer() [or ui.row() fallback]
      │   ├── nav_item("Home", "/", "home")
      │   ├── nav_item("Gestiones", "/gestiones", "assignment")
      │   ├── nav_item("Nueva Gestión", "/gestiones/nueva", "add_circle")
      │   ├── nav_item("Detalle Gestión", "/gestiones/{id}", "visibility")  # placeholder
      │   ├── nav_item("Pagos", "/pagos", "payments")
      │   ├── nav_item("Períodos", "/periodos", "calendar_month")
      │   └── nav_item("Reportes", "/reportes", "bar_chart")
      └── [content area] ← yielded
          └── page-specific content
```

## File Changes

| File | Action | Description |
|------|--------|-------------|
| `src/ui/components/shell.py` | **Create** | `AppShell` class with `__enter__`/`__exit__`, `_render_header()`, `_render_sidebar()`, `_nav_item()` helpers |
| `src/ui/pages/home.py` | **Modify** | Replace manual auth+navbar with `with AppShell():`; add metrics: total claims, recent 5, stat cards (pending SOS, active payments, current period); empty state support |
| `src/ui/pages/gestiones.py` | **Create** | Placeholder page at `/gestiones` |
| `src/ui/pages/gestiones_nueva.py` | **Create** | Placeholder at `/gestiones/nueva` |
| `src/ui/pages/gestiones_detalle.py` | **Create** | Placeholder at `/gestiones/{id}` |
| `src/ui/pages/pagos.py` | **Create** | Placeholder at `/pagos` |
| `src/ui/pages/periodos.py` | **Create** | Placeholder at `/periodos` |
| `src/ui/pages/reportes.py` | **Create** | Placeholder at `/reportes` |
| `src/ui/components/navbar.py` | **Modify/Keep** | `crear_navbar` is subsumed by AppShell header; keep file, mark deprecated or remove its call from home.py |
| `main.py` | **Modify** | Register all 7 pages; remove old `register_home_page()` + navbar calls |

## Interfaces / Contracts

```python
class AppShell:
    def __init__(self, title: str = "Gestiones SOS") -> None:
        ...

    def __enter__(self) -> None:
        # 1. Auth guard — read app.storage.user["token"]
        # 2. Dark mode — ui.dark_mode().enable()
        # 3. Header — self._render_header()
        # 4. Sidebar — self._render_sidebar()
        ...

    def __exit__(self, *args) -> None:
        pass  # Nothing to tear down; page lifecycle manages cleanup
```

```python
# Placeholder page pattern
def register_gestiones_page() -> None:
    @ui.page("/gestiones")
    def gestiones_page() -> None:
        with AppShell():
            ui.label("Gestiones").classes("text-2xl font-bold")
```

## Dark Theme — Edge Cases

- `ui.dark_mode().enable()` globally — call once, subsequent calls are no-ops.
- Override hardcoded light-bg classes: add `ui.query("body").classes("!bg-gray-900")` and target common light-classes (`text-blue-800`, `text-gray-600`, `bg-gray-100`) with dark equivalents via `ui.add_head_html("<style>...")`.
- Existing auth pages (login, register) keep their light styling — they run outside AppShell.

## Testing Strategy

| Layer | What to Test | Approach |
|-------|-------------|----------|
| Unit | `AppShell.__enter__` auth guard | Mock `app.storage.user`, assert redirect when token missing |
| Unit | Sidebar nav items rendered | Capture elements via NiceGUI test client |
| Unit | Header shows user name | Set `app.storage.user["user_name"]`, assert label exists |
| Integration | Home metrics with empty repos | Use `InMemoryClaimRepository` (follows same pattern as `InMemoryUserRepository` in tests), wire via Container, assert empty-state renders |
| Integration | Home metrics with data | Seed repos, assert counts + recent list render |
| E2E | All placeholder pages render | Navigate to each route, assert no HTTP errors |

## Migration / Rollout

1. **Create** `shell.py` — no external impact, safe to ship first
2. **Create** placeholder pages — each is a tiny page with AppShell
3. **Modify** `home.py` — switch to AppShell, add metrics
4. **Modify** `main.py` — register all pages, remove old navbar usage
5. Validate: `ruff check .` + manual nav through all routes

No data migration needed. Rollback: restore `main.py` + `home.py` from git.

## Open Questions

- None
