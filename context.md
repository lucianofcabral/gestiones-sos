# Contexto del Proyecto: gestiones-sos-hex

## Descripción General

Aplicación de gestión de reclamos de servicios de auxilio (claims) para una compañía de seguros.
Permite registrar, gestionar y hacer seguimiento de gestiones SOS, pagos, períodos de facturación y documentos adjuntos.

- **Framework UI:** [NiceGUI](https://nicegui.io/) (Python, corre en puerto 8080)
- **Base de datos:** PostgreSQL (acceso vía SQLAlchemy Core — sin ORM)
- **Arquitectura:** Hexagonal (Ports & Adapters)
- **Python:** ≥ 3.13
- **Gestor de paquetes/entorno:** `uv` (`.python-version`, `uv.lock`)
- **Migraciones:** Alembic
- **Linter:** Ruff (`line-length = 88`, `target-version = "py313"`)
- **Tests:** pytest (`tests/`)

---

## Arquitectura Hexagonal

```
src/
├── domain/           # Núcleo de negocio (sin dependencias externas)
│   ├── models/       # Entidades Pydantic
│   ├── ports/        # Interfaces (Protocols) para repositorios y servicios
│   ├── services/     # Servicios de dominio (vacío por ahora)
│   ├── enums.py      # Enums del dominio
│   └── exceptions.py # Excepciones de dominio
│
├── application/      # Casos de uso
│   ├── use_cases/
│   │   ├── auth/     # Login, Register, Logout, Me
│   │   └── claims/   # RegistrarGestionSOS, EliminarGestionSOS
│   └── orchestrators/ # (vacío por ahora)
│
├── adapters/         # Implementaciones de los ports
│   ├── auth/         # JwtService (TokenPort), PasswordAdapter (PasswordPort)
│   ├── persistence/  # Repositorios PostgreSQL e in-memory
│   └── logging/
│
├── infrastructure/   # Configuración técnica
│   ├── container.py  # IoC Container (Singleton)
│   └── database/
│       ├── connection.py  # get_connection() → SQLAlchemy engine
│       └── tables.py      # Definición de tablas SQLAlchemy Core
│
└── ui/               # Capa de presentación (NiceGUI)
    ├── pages/        # home.py, login.py, register.py
    ├── routes/       # auth.py → AuthRouter + rutas REST /api/auth/*
    └── components/
```

---

## Entidades del Dominio (`src/domain/models/entities.py`)

Todas las entidades son modelos **Pydantic** con UUIDs como PK.

| Entidad         | Descripción |
|----------------|-------------|
| `User`          | Usuario del sistema (email único, password hasheado) |
| `Claim`         | Siniestro base: reclamante, patente, póliza, monto reclamado |
| `SosClaim`      | Gestión SOS vinculada a un `Claim`: número de gestión, categoría, estado, ITR |
| `GroupClaim`    | Agrupación de siniestros |
| `ClaimKind`     | Tipo de siniestro (SOS, Tres Arroyos, Ad-hoc) |
| `Agent`         | Agente (SM, prestador, SOS, asegurado) |
| `PaymentVia`    | Vía de pago (transferencia, NC) |
| `Payment`       | Pago asociado a un `Claim` |
| `CreditNote`    | Nota de crédito (NC) asociada a un `Payment` y un `Period` |
| `Invoice`       | Factura vinculada a un `Period` |
| `Period`        | Período mensual (año + mes); calcula primer/último día y período siguiente |
| `Document`      | Documento adjunto (hash, nombre, mime, tamaño) |
| `DocumentEntity`| Relación polimórfica documento ↔ entidad (via `DocumentTypeEnum`) |

---

## Ports (Interfaces)

### `src/domain/ports/auth.py`
- `PasswordPort`: `verify_password`, `hash_password`
- `TokenPort`: `create_token`, `verify_token`, `invalidate_token`

### `src/domain/ports/repositories.py`
Todos los repos heredan de `BaseRepo[T]` con: `add`, `get_by_id`, `delete`, `update`, `get_all`, `exists`, `get_by_ids`.

Repos específicos: `UserRepoPort`, `PeriodRepoPort`, `BillingRepoPort`, `AgentRepoPort`, `PaymentViaRepoPort`, `ClaimKindRepoPort`, `ClaimRepoPort`, `SosClaimRepoPort`, `GroupClaimRepoPort`, `PaymentRepoPort`, `NcPaymentRepoPort`, `DocumentRepoPort`.

### `src/domain/ports/uow.py`
`UnitOfWork` (ABC): context manager que expone `claims` y `sos_claims`; hace `commit` o `rollback` automáticamente.

---

## Adapters

### Auth
- `JwtService` (`src/adapters/auth/jwt_service.py`): tokens HS256, 60 min de expiración, blacklist en memoria. Implementa `TokenPort`.
- `PasswordAdapter` (`src/adapters/auth/password_adapter.py`): bcrypt vía `passlib`. Implementa `PasswordPort`.

### Persistence
- Repositorios **PostgreSQL** (SQLAlchemy Core): `PostgreSQLUserRepository`, `PostgreSQLClaimRepository`, `PostgreSQLSosClaimRepository`, `PostgreSQLUnitOfWork`.
- Repositorios **in-memory**: para tests sin base de datos.

---

## Casos de Uso

### Auth (`src/application/use_cases/auth/`)
| Clase      | Input               | Output             |
|-----------|---------------------|--------------------|
| `Login`   | email, password     | token, user info   |
| `Register`| user_name, email, password | user info   |
| `Me`      | user_id (UUID)      | user info + active |
| `Logout`  | token               | success + message  |

### Claims (`src/application/use_cases/claims/`)
- `RegistrarGestionSOS`: crea atómicamente un `Claim` + `SosClaim` vía UoW. Valida que el número de gestión no exista.
- `EliminarGestionSOS`: elimina una gestión SOS.

---

## Infrastructure

### Container (`src/infrastructure/container.py`)
Singleton `Container` que instancia y conecta todos los adapters:
- `_user_repo` → `PostgreSQLUserRepository`
- `_password_adapter` → `PasswordAdapter`
- `_jwt_service` → `JwtService` (usa `JWT_SECRET` de env)
- `_auth_router` → `AuthRouter`

### Base de datos
- Tablas definidas en `src/infrastructure/database/tables.py` (SQLAlchemy Core Metadata).
- Tablas activas: `users`, `claims`, `sos_claims`.
- Migraciones con Alembic (`alembic/`).

---

## UI (NiceGUI)

### Páginas
- `/login` → `register_login_page()`
- `/register` → `register_register_page()`
- `/` (home) → `register_home_page()`

### API REST (montada en NiceGUI via `@app.post/get`)
| Método | Ruta                  | Descripción       |
|--------|-----------------------|-------------------|
| POST   | `/api/auth/login`     | Login con email/password → token |
| POST   | `/api/auth/register`  | Registro nuevo usuario |
| GET    | `/api/auth/me`        | Info del usuario autenticado |
| POST   | `/api/auth/logout`    | Invalida el token |

---

## Variables de Entorno (`.env`)

```
JWT_SECRET=<secreto largo>
STORAGE_SECRET=<secreto para NiceGUI storage>
DATABASE_URL=postgresql://sos_user:sos_pass@localhost/gestiones_sos
```

---

## Enums (`src/domain/enums.py`)

| Enum               | Valores |
|-------------------|---------|
| `DocumentTypeEnum` | user, period, invoice, agent, payment_via, claim_kind, claim, sos_claim, group_claim, payment, credit_note |
| `UserStatusEnum`   | active, inactive, pending |
| `ClaimKindEnum`    | sos, tres_arroyos, adhoc |

---

## Comandos Útiles

```bash
# Instalar dependencias
uv sync

# Correr la aplicación
python main.py

# Linter
uv run ruff check .
uv run ruff format .

# Tests
uv run pytest

# Migraciones
uv run alembic upgrade head
uv run alembic revision --autogenerate -m "descripcion"
```

---

## Convenciones del Proyecto

- **Modelos de dominio:** Pydantic `BaseModel`, nunca SQLAlchemy ORM.
- **Repositorios:** SQLAlchemy Core (no ORM). Cada método abre y cierra su propia conexión vía `get_connection()`.
- **Puertos:** Python `Protocol` (structural subtyping), no clases abstractas (excepto `UnitOfWork` que usa ABC).
- **Inyección de dependencias:** manual vía constructor; el `Container` es el único punto de ensamblaje.
- **Errores de negocio:** se lanzan como `ValueError` desde los casos de uso.
- **Tests:** solo `tests/test_auth.py` por ahora; usan repositorios in-memory.
- **Idioma:** código en inglés, comentarios/UI en español.
