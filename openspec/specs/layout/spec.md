# Layout Specification — App Shell, Theme & Route Protection

## Purpose

Provide a consistent dark-themed layout that wraps every authenticated page with route protection, removing ad-hoc per-page auth checks and light-bg assumptions.

## Requirements

### Requirement: AppShell Context Manager

The system MUST provide an `AppShell` context manager that wraps each page's content with a shared layout: dark theme, sidebar, top header, and content area.

#### Scenario: Page wrapped in AppShell
- GIVEN an authenticated user navigates to any protected route
- WHEN the page function executes and enters `with AppShell():`
- THEN the system renders the sidebar, header, and the page's content in a main area

#### Scenario: AppShell does not wrap login or register
- GIVEN the login or register page
- WHEN those pages render
- THEN AppShell MUST NOT be applied — they have standalone layout

### Requirement: Dark Theme Always On

The system MUST call `ui.dark_mode().enable()` on every page that uses AppShell. The theme MUST be dark always — no toggle, no light mode.

#### Scenario: Dark theme enabled on entry
- GIVEN AppShell context manager enters
- WHEN `ui.dark_mode().enable()` executes
- THEN all page elements render with dark background and light text
- AND all hardcoded light-bg classes (e.g. `bg-blue-700`, `bg-gray-100`, `text-blue-800`) MUST be overridden or removed

#### Scenario: No light-bg leak
- GIVEN a page that previously set `ui.query("body").classes("bg-gray-100")`
- WHEN AppShell enables dark mode
- THEN those light-background classes MUST NOT override the dark theme
- AND the system overrides or neutralizes them

### Requirement: Route Protection

On AppShell entry, the system MUST check `app.storage.user["token"]`. If absent, the system MUST redirect to `/login` via `ui.open()`.

#### Scenario: Authenticated user passes through
- GIVEN a user with a token in `app.storage.user`
- WHEN entering a protected route via AppShell
- THEN the token check passes
- AND the page content renders normally

#### Scenario: Unauthenticated user redirected to login
- GIVEN a user with NO token in `app.storage.user`
- WHEN entering any protected route
- THEN the system calls `ui.open("/login")`
- AND the page content does NOT render

#### Scenario: Token present but expired
- GIVEN a user with a token, but the token is expired
- WHEN entering a protected route
- THEN the system redirects to `/login` — the storage check does not validate token expiry
- (Token validation is handled by login/me endpoints)
