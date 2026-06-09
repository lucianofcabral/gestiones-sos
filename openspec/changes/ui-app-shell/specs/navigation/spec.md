# Navigation Specification — Sidebar, Header & Page Routing

## Purpose

Provide consistent sidebar navigation and top header across all authenticated pages, and register all page routes in a centralized manner via `main.py`.

## Requirements

### Requirement: Sidebar Navigation

The system MUST render a sidebar via `ui.left_drawer()` that contains navigation links to all major sections.

#### Scenario: Sidebar visible on protected pages
- GIVEN an authenticated user viewing any protected page
- WHEN the page renders
- THEN a left drawer sidebar is visible with navigation links

#### Scenario: Sidebar expandable
- GIVEN the sidebar is rendered
- WHEN the user clicks the hamburger/toggle icon
- THEN the sidebar expands or collapses

#### Scenario: Sidebar fallback
- GIVEN `ui.left_drawer` is not available or fails
- WHEN the page renders
- THEN the system falls back to a `ui.row()`-based sidebar layout so navigation is still accessible

#### Scenario: Sidebar contains correct links
- GIVEN the sidebar is visible
- WHEN the user inspects the navigation items
- THEN the sidebar SHALL contain links to: Home (`/`), Gestiones (`/gestiones`), Pagos (`/pagos`), Períodos (`/periodos`), Reportes (`/reportes`)
- AND a logout button

#### Scenario: Logout from sidebar
- GIVEN an authenticated user
- WHEN the user clicks "Salir" in the sidebar
- THEN the system clears `app.storage.user` and navigates to `/login`

### Requirement: Top Header

The system MUST render a top header via `ui.header()` showing the application title and current user name.

#### Scenario: Header visible
- GIVEN any protected page
- WHEN the page renders
- THEN a header shows "Gestiones SOS" and the logged-in user's name

### Requirement: Placeholder Pages

The system MUST register placeholder pages for all routes listed in the proposal without errors.

#### Scenario: All placeholder pages render
- GIVEN the following routes: `/gestiones`, `/gestiones/nueva`, `/gestiones/{id}`, `/pagos`, `/periodos`, `/reportes`
- WHEN each route is visited by an authenticated user
- THEN the page renders without errors, showing a placeholder title and the AppShell layout

#### Scenario: Unauthenticated access to placeholder pages
- GIVEN a user with no token
- WHEN visiting any placeholder route
- THEN the system redirects to `/login` via AppShell's route protection

### Requirement: Centralized Page Registration

The system MUST register all page routes in `main.py` in a single block, replacing the current ad-hoc per-page registration.

#### Scenario: Existing pages still work
- GIVEN the page registration is refactored
- WHEN the application starts
- THEN login, register, and home pages register correctly and are reachable
