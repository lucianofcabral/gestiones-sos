## Exploration: Codebase Overview

### Current State

The system is a hexagonal architecture (Ports & Adapters) Python application for managing SOS insurance claims. It currently handles **authentication** (register, login, logout, me) and has the foundation for **SOS claim management** (register, delete).

**Layers:**
- **Domain** (`src/domain/`): Pure Pydantic entities (no external dependencies), Protocol ports for repos/services, enums, and an empty `exceptions.py` and `services/`.
- **Application** (`src/application/`): Use case classes with explicit Input/Output DTOs. Auth use cases (Login, Register, Me, Logout) are complete. Claims use cases (RegistrarGestionSOS, EliminarGestionSOS) exist but have issues. Empty `orchestrators/` and `loggers/` directories indicate planned but unimplemented layers.
- **Adapters** (`src/adapters/`): Implementations of domain ports. `JwtService` (TokenPort), `PasswordAdapter` (PasswordPort), PostgreSQL repositories (User, Claim, SosClaim), and in-memory repositories for testing. `PostgreSQLUnitOfWork` implements the Unit of Work pattern.
- **Infrastructure** (`src/infrastructure/`): Singleton Container for dependency injection, SQLAlchemy Core table definitions, and connection management.
- **UI** (`src/ui/`): NiceGUI pages (login, register, home) and REST API routes (`/api/auth/*`). An `AuthRouter` bridges the gap between the UI and use cases.

**Data model:** Users (auth), Claims (base claim info), SosClaims (SOS-specific data linked to a Claim via FK). 12 domain entities defined but only users, claims, and sos_claims have DB tables via Alembic migrations.

**Key architectural patterns:**
1. **Ports & Adapters via Protocols**: Domain defines interfaces as Python Protocols (structural subtyping). Adapters implement them without needing explicit inheritance.
2. **Repository pattern**: Adapter layer provides data access; domain defines the contract.
3. **Unit of Work**: `PostgreSQLUnitOfWork` wraps multiple repository operations in a single DB transaction (used by RegistrarGestionSOS for atomic Claim+SosClaim creation).
4. **Use Case pattern**: Each operation is a class with `execute(input) → output`. Clear separation of orchestration from business logic.
5. **Manual DI via Singleton Container**: `Container` assembles all dependencies. However, UI pages also call `get_container()` directly (service locator anti-pattern).

**Testing:** Single test file (`tests/test_auth.py`) with 7 tests. Uses in-memory repos and fake password/token ports. Tests register, login, me, logout flows. Good pattern but minimal coverage — no tests for claims use cases, no integration tests.

### Affected Areas
- `src/application/use_cases/claims/eliminar_gestion_sos.py` — BUG: file is a direct copy of `registrar_gestion_sos.py`; same class names, same logic. Delete/eliminate use case is NOT implemented.
- `tests/test_auth.py` — Only existing tests; tests auth use cases with in-memory fakes. No claims tests.
- `src/domain/exceptions.py` — Empty file. All business errors raised as generic `ValueError`.
- `src/domain/services/` — Empty directory.
- `src/application/orchestrators/` — Empty directory.
- `src/application/loggers/` — Empty directory.
- `src/adapters/logging/` — Empty directory.
- `src/adapters/persistence/postgresql_user_repository.py` — Does NOT support UoW; always commits independently. Only user repo lacks the `_get_conn(conn=None)` pattern.
- `src/adapters/auth/jwt_service.py` — `_purge_expired` method exists but is NEVER called. Blacklist grows unbounded.
- `src/ui/pages/login.py`, `register.py`, `home.py` — Pages call `get_container()` directly (service locator) instead of receiving dependencies.
- `src/ui/components/navbar.py` — Logout clears NiceGUI storage but does NOT call the logout use case to invalidate the token server-side.
- `src/adapters/persistence/postgresql_sos_claim_repository.py` — Forward-reference `"sa.Connection | None"` uses runtime string annotation but file lacks `from __future__ import annotations`.

### Approaches
1. **Fix the copy-paste bug in EliminarGestionSOS** — Low effort, immediate fix. Replace the copy of RegistrarGestionSOS with the actual delete logic (delete SosClaim + Claim by IDs, respecting UoW).
   - Pros: Quick win, unblocks claims functionality
   - Cons: None
   - Effort: Low

2. **Add domain-specific exceptions** — Replace ValueError with typed exceptions.
   - Pros: Better error handling, cleaner domain layer
   - Cons: Requires updating all use cases and adapters
   - Effort: Medium

3. **Add integration/e2e tests for claims use cases** — Test RegistrarGestionSOS and EliminarGestionSOS with in-memory repos and UoW fakes.
   - Pros: Covers critical functionality
   - Cons: Need to implement in-memory UoW first
   - Effort: Medium

4. **Extract service locator from UI pages** — Inject AuthRouter into pages instead of calling `get_container()`.
   - Pros: Cleaner DI, testable UI
   - Cons: NiceGUI page registration pattern makes this awkward
   - Effort: Medium

5. **Add test coverage** — Expand to cover claims use cases, edge cases, and negative paths.
   - Pros: Foundation for safe refactoring
   - Cons: Time investment
   - Effort: Medium

6. **Fix UoW inconsistency** — Make PostgreSQLUserRepository participate in external transactions like the other repos.
   - Pros: Consistent pattern across all repos
   - Cons: Breaking change to how user operations work
   - Effort: Medium

### Recommendation
Start with approach 1 (fix EliminarGestionSOS) as it's clearly a bug. Then approach 3 (claims tests) to solidify the claims domain. Follow with approach 2 (domain exceptions) since it's a natural next step for a learning developer to understand typed errors. Skip approaches 4-6 unless the user specifically wants to explore DI or testing patterns.

### Risks
- The copy-paste bug in EliminarGestionSOS means delete functionality is completely broken/misimplemented.
- No integration tests means DB-layer bugs go undetected.
- Empty exceptions.py means all errors are `ValueError` — no way to distinguish between domain errors, validation errors, and system errors.
- UoW inconsistency could lead to partial data writes (UserRepo always commits independently, others participate in transactions).
- JWT blacklist grows unbounded — `_purge_expired` never called.

### Ready for Proposal
Yes — the immediate next step is fixing the EliminarGestionSOS bug and adding tests for the claims domain. Ready to proceed to sdd-propose for "Fix EliminarGestionSOS and add claims test coverage".
