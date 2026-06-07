# Design: payments-module

## Technical Approach

Add soft-delete (`active` field) to existing `Payment` and `CreditNote` entities, add `_Activatable` to both port protocols, implement a domain service for closed-period eligibility checks, and inject a payment guard into `EliminarGestionSOS`. Two new tables (`payments`, `nc_payments`), four repo implementations (SQLAlchemy + in-memory × 2), and CRUD use cases following the existing `RegistrarGestionSOS`/`EliminarGestionSOS` pattern.

## Architecture Decisions

| Decision | Choice | Alternatives | Rationale |
|----------|--------|-------------|-----------|
| Port change for PaymentRepoPort | Add `_Activatable` + `inactivatable` | Separate service | Existing repos use `_Activatable` mixin for soft-delete — consistent with all other entities |
| Port change for NcPaymentRepoPort | Add `_Activatable` + `mark_delivered` | Update use case with field exclusion | `delivered` has a dedicated lifecycle — mirroring the existing pattern of business-specific operations |
| Domain service signature | `(bool, str)` tuple | Custom exception, enum | Simplest contract for UI consumption; the string is a human-readable reason |
| Payment update field scope | All non-identity fields | Restricted whitelist | Proposal confirmed no business rule for update restrictions — identity fields excluded by convention |
| NC validation approach | `PaymentViaRepoPort.get_nc()` + `AgentRepoPort.get_sos/get_sm()` | Field on PaymentVia entity | Existing ports already expose these lookups — zero new dependencies |
| Claim deletion guard | Inject PaymentRepoPort in constructor | Domain event, UoW hook | Matches existing pattern (constructor DI), no new infra needed |

## Data Flow

```
┌──────────────────────┐
│   RegistrarPago      │
│  (create payment)    │
├──────────────────────┤
│ 1. Validate NC:      │
│    PaymentViaRepo    │
│    → get_nc()        │
│    AgentRepoPort     │
│    → get_sos/sm()   │
│ 2. PaymentRepo.add() │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│  InactivarPago       │
│  (soft-delete)       │
├──────────────────────┤
│ 1. PaymentRepo       │
│    → get_by_id()     │
│ 2. CanInactivateSvc  │
│    → evaluate()      │
│ 3. PaymentRepo       │
│    → inactivate()    │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│  EliminarGestionSOS  │
│  (modified)          │
├──────────────────────┤
│ 1. ClaimRepo         │
│    → get_by_id()     │
│ 2. PaymentRepo       │
│    → get_by_claim_id │
│    → all active=False│
│ 3. ClaimRepo         │
│    → inactivate()    │
└──────────────────────┘
```

## File Changes

| File | Action | Description |
|------|--------|-------------|
| `src/domain/models/entities.py` | Modify | Add `active: bool = True` to `Payment` and `CreditNote` |
| `src/domain/ports/repositories.py` | Modify | Add `_Activatable` to `PaymentRepoPort` and `NcPaymentRepoPort`; add `get_by_period_id` to `BillingRepoPort`; add `mark_delivered`, `inactivatable` |
| `src/domain/services/can_inactivate_payment.py` | Create | Domain service: `evaluate(payment_id) -> (bool, str)` |
| `src/application/use_cases/payments/registrar_pago.py` | Create | Create Payment with NC validation |
| `src/application/use_cases/payments/inactivar_pago.py` | Create | Inactivate Payment via domain service |
| `src/application/use_cases/payments/obtener_pago.py` | Create | Get Payment by ID |
| `src/application/use_cases/payments/listar_pagos.py` | Create | List all Payments |
| `src/application/use_cases/payments/actualizar_pago.py` | Create | Update non-identity Payment fields |
| `src/application/use_cases/payments/activar_pago.py` | Create | Set Payment `active=True` |
| `src/application/use_cases/payments/registrar_nc_pago.py` | Create | Create NcPayment |
| `src/application/use_cases/payments/obtener_nc_pago.py` | Create | Get NcPayment by ID |
| `src/application/use_cases/payments/listar_nc_pagos.py` | Create | List all NcPayments |
| `src/application/use_cases/payments/actualizar_nc_pago.py` | Create | Update non-identity NcPayment fields |
| `src/application/use_cases/payments/marcar_nc_entregado.py` | Create | Mark NcPayment delivered |
| `src/application/use_cases/payments/activar_nc_pago.py` | Create | Set NcPayment `active=True` |
| `src/application/use_cases/payments/inactivar_nc_pago.py` | Create | Set NcPayment `active=False` |
| `src/application/use_cases/claims/eliminar_gestion_sos.py` | Modify | Add `payment_repo` param, guard before inactivate |
| `src/adapters/persistence/sqlalchemy_payment_repository.py` | Create | SQLAlchemy Core impl for PaymentRepoPort |
| `src/adapters/persistence/inmemory_payment_repository.py` | Create | In-memory impl for tests |
| `src/adapters/persistence/sqlalchemy_ncpayment_repository.py` | Create | SQLAlchemy Core impl for NcPaymentRepoPort |
| `src/adapters/persistence/inmemory_ncpayment_repository.py` | Create | In-memory impl for tests |
| `src/adapters/persistence/sqlalchemy_billing_repository.py` | Modify | Add `get_by_period_id` |
| `src/adapters/persistence/inmemory_billing_repository.py` | Modify | Add `get_by_period_id` |
| `src/infrastructure/database/tables.py` | Modify | Add `payments` and `nc_payments` tables |
| `src/infrastructure/container.py` | Modify | Wire new repos and use cases |
| `alembic/versions/xxxx_create_payments_tables.py` | Create | Migration for both tables |
| `tests/test_payments.py` | Create | Unit tests for Payment + NcPayment use cases |
| `tests/test_claims.py` | Modify | Update tests for payment guard |

## Interfaces / Contracts

### Domain entity changes (entities.py)

```python
class Payment(BaseModel):
    payment_id: UUID = Field(default_factory=uuid4)
    claim_id: UUID
    payer_id: UUID
    payment_via_id: UUID
    payee_id: UUID
    amount: float = Field(0, ge=0)
    active: bool = True                     # NEW
    created_date: datetime = Field(default_factory=datetime.now)

class CreditNote(BaseModel):
    nc_payment_id: UUID = Field(default_factory=uuid4)
    payment_id: UUID
    period_id: UUID
    delivered: bool = False
    active: bool = True                     # NEW
    created_date: datetime = Field(default_factory=datetime.now)
```

### Port changes (repositories.py)

```python
class PaymentRepoPort(BaseRepo[Payment], _Activatable[Payment], Protocol):
    def deleteable(self, id: UUID) -> bool: ...
    def inactivatable(self, id: UUID) -> bool: ...         # NEW
    def get_by_claim_id(self, claim_id: UUID) -> list[Payment]: ...
    def get_by_date_range(self, start_date: str, end_date: str) -> list[Payment]: ...
    def get_by_amount_range(self, min_amount: float, max_amount: float) -> list[Payment]: ...

class NcPaymentRepoPort(BaseRepo[CreditNote], _Activatable[CreditNote], Protocol):
    def deleteable(self, id: UUID) -> bool: ...
    def mark_delivered(self, id: UUID) -> bool: ...        # NEW
    def get_by_payment_id(self, payment_id: UUID) -> CreditNote | None: ...
    def get_by_period_id(self, period_id: UUID) -> list[CreditNote]: ...

class BillingRepoPort(BaseRepo[Invoice], _DocReachable[Invoice], Protocol):
    def get_by_period_id(self, period_id: UUID) -> list[Invoice]: ...  # NEW
```

### Domain service

```python
class CanInactivatePaymentService:
    def __init__(self, nc_payment_repo: NcPaymentRepoPort,
                 billing_repo: BillingRepoPort) -> None: ...
    def evaluate(self, payment_id: UUID) -> tuple[bool, str]: ...
```

### Use case: InactivarPago

```python
class InactivarPagoInput(BaseModel):
    payment_id: UUID

class InactivarPagoOutput(BaseModel):
    payment_id: UUID
    success: bool

class InactivarPago:
    def __init__(self, payment_repo: PaymentRepoPort,
                 can_inactivate_svc: CanInactivatePaymentService) -> None: ...
    def execute(self, input_data: InactivarPagoInput) -> InactivarPagoOutput: ...
```

### Modified: EliminarGestionSOS

```python
class EliminarGestionSOS:
    def __init__(self, claim_repo: ClaimRepoPort,
                 payment_repo: PaymentRepoPort) -> None:  # NEW param
        ...
    def execute(self, input_data: EliminarGestionSOSInput) -> EliminarGestionSOSOutput:
        claim = self._claim_repo.get_by_id(input_data.claim_id)
        if claim is None:
            raise ValueError("Claim not found")
        # NEW: payment guard
        payments = self._payment_repo.get_by_claim_id(input_data.claim_id)
        if any(p.active for p in payments):
            raise ValueError("Claim has active payments")
        self._claim_repo.inactivate(input_data.claim_id)
        ...
```

## Table definitions (tables.py)

```python
payments = sa.Table(
    "payments", metadata,
    sa.Column("payment_id", sa.UUID, primary_key=True),
    sa.Column("claim_id", sa.UUID, sa.ForeignKey("claims.claim_id"), nullable=False),
    sa.Column("payer_id", sa.UUID, nullable=False),
    sa.Column("payee_id", sa.UUID, nullable=False),
    sa.Column("payment_via_id", sa.UUID, nullable=False),
    sa.Column("amount", sa.Numeric(12, 2), nullable=False),
    sa.Column("active", sa.Boolean, nullable=False, server_default="true"),
    sa.Column("created_date", sa.DateTime, nullable=False, server_default=sa.func.now()),
)

nc_payments = sa.Table(
    "nc_payments", metadata,
    sa.Column("nc_payment_id", sa.UUID, primary_key=True),
    sa.Column("payment_id", sa.UUID, sa.ForeignKey("payments.payment_id"), nullable=False),
    sa.Column("period_id", sa.UUID, sa.ForeignKey("periods.period_id"), nullable=False),
    sa.Column("delivered", sa.Boolean, nullable=False, server_default="false"),
    sa.Column("active", sa.Boolean, nullable=False, server_default="true"),
    sa.Column("created_date", sa.DateTime, nullable=False, server_default=sa.func.now()),
)
```

## Alembic Migration

Explicit `op.create_table()` matching the above. Note: there is no existing `periods` table yet — `nc_payments.period_id` FK references a table that must exist. If `periods` does not exist, the migration must create it first. However, `Period` model exists in entities — confirm `periods` table already deployed or add to this migration.

## Container Wiring

```python
class Container:
    def __init__(self):
        # ... existing ...
        self._payment_repo = SqlAlchemyPaymentRepository()
        self._nc_payment_repo = SqlAlchemyNcPaymentRepository()
        self._billing_repo = SqlAlchemyBillingRepository()
        self._can_inactivate_svc = CanInactivatePaymentService(
            nc_payment_repo=self._nc_payment_repo,
            billing_repo=self._billing_repo,
        )
        self._eliminar_gestion_sos = EliminarGestionSOS(
            claim_repo=self._claim_repo,
            payment_repo=self._payment_repo,
        )
        # Payment use cases
        self._registrar_pago = RegistrarPago(
            payment_repo=self._payment_repo,
            payment_via_repo=...,   # needs to be wired
            agent_repo=...,         # needs to be wired
        )
        self._inactivar_pago = InactivarPago(
            payment_repo=self._payment_repo,
            can_inactivate_svc=self._can_inactivate_svc,
        )
```

Note: `PaymentViaRepoPort` and `AgentRepoPort` are already declared in ports but may not have SQLAlchemy repos wired in Container yet. The `RegistrarPago` NC validation depends on these — if unreachable, validate inline with `get_by_name` lookups.

## Testing Strategy

| Layer | What | Approach |
|-------|------|----------|
| Unit | Payment CRUD use cases | InMemoryPaymentRepository, assert create/update/inactivate/activate |
| Unit | NcPayment CRUD use cases | InMemoryNcPaymentRepository, assert create/update/mark_delivered |
| Unit | CanInactivatePaymentService | Mock repos for 3 scenarios (no NcPayment, NcPayment no invoice, period closed) |
| Unit | EliminarGestionSOS payment guard | InMemoryPaymentRepository, seed active/inactive payments |
| Unit | RegistrarPago NC validation | InMemory repos for PaymentVia, Agent |

## Risk Analysis

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| `periods` table not deployed | Medium | Blocking | Check alembic history; create periods table in same migration if missing |
| `PaymentViaRepoPort`/`AgentRepoPort` not wired in Container | High | Broken NC validation | Delay NC validation wiring or add `_build_*` factories in Container |
| `RegistrarPago` needs PaymentVia+Agent repos but they're unavailable | Medium | Feature incomplete | Make NC validation optional at runtime (skip if repos not configured) |
| `inactivatable` duplicates `deleteable` semantics | Low | Confusion | `inactivatable` checks NC references; `deleteable` is reserved. Keep both until consolidated |

## Open Questions

- [ ] Does the `periods` table exist in the deployed DB? If not, the migration must create it.
