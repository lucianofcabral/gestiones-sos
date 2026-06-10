# Design: Payment CRUD — Update & Activate

## Technical Approach

Add two application use cases (`ActualizarPago`, `ActivarPago`) with shared business rules extracted to **domain services**, following the same pattern as `CanInactivatePaymentService`.

Two new domain services:
- **`PaymentUpdateRules`** — encapsulates editability rules (what fields can change when NC exists, NC-via guard)
- **`CanActivatePaymentService`** — symmetric to `CanInactivatePaymentService`, checks claim-active gate

Entity change: `Payment.amount` constraint from `ge=0` to `gt=0` (the rule belongs to the domain model, not the use case).

## Architecture Decisions

| Option | Tradeoff | Decision |
|--------|----------|----------|
| Rules in use case vs. domain service | Inline = simpler but leaks domain logic; service = reusable, testable, proper hexagonal | **Domain service** — follows `CanInactivatePaymentService` precedent, keeps business rules in the domain layer |
| `amount > 0` in entity vs. use case | Entity validation catches it at the boundary for ALL paths; UC-only misses direct construction | **Entity constraint** — change `ge=0` to `gt=0` on `Payment.amount` |
| Single vs. split domain services | Single `PaymentRules` = fewer files; split = SRP, each has one reason to change | **Split** — `PaymentUpdateRules` for editability, `CanActivatePaymentService` for activation gate |
| `CanActivatePaymentService` return type | `bool` (simple) vs. `tuple[bool, str]` (info) | **`tuple[bool, str]`** — matches `CanInactivatePaymentService` convention |

## Data Flow

```
ActualizarPago:
  execute(input) ──→ PaymentRepoPort.get_by_id(payment_id)
                    ──→ PaymentUpdateRules.validate(input_data, existing_nc, existing_payment_via)
                          │ raises ValueError on violation
                    ──→ Build updated Payment model
                    ──→ PaymentRepoPort.update(payment_id, model)
                    ──→ return ActualizarPagoOutput(success=True/False)

ActivarPago:
  execute(input) ──→ PaymentRepoPort.get_by_id(payment_id)
                    ──→ CanActivatePaymentService.execute(payment)
                          │ uses ClaimRepoPort internally
                    ──→ PaymentRepoPort.activate(payment_id)
                    ──→ return ActivarPagoOutput(success=True/False)
```

## Business Rule Enforcement

| Rule | Layer | Mechanism |
|------|-------|-----------|
| `amount` must always be > 0 | **Entity** (`Payment`) | `Field(gt=0)` — Pydantic validates on construction |
| `payment_via_id` cannot change to NC (no NC case) | **Domain service** (`PaymentUpdateRules`) | If no NC exists AND `payment_via_id` provided → check `PaymentViaRepoPort.get_nc()` → `ValueError` |
| Only `amount` editable when NC exists | **Domain service** (`PaymentUpdateRules`) | If NC exists AND non-amount fields provided → `ValueError` |
| Claim must be active to reactivate | **Domain service** (`CanActivatePaymentService`) | `ClaimRepoPort.get_by_id(payment.claim_id)` → if not `active` → return `(False, reason)` |

## File Changes

| File | Action | Description |
|------|--------|-------------|
| `src/domain/models/entities.py` | Modify | `Payment.amount`: `gt=0` instead of `ge=0` |
| `src/domain/services/payment_update_rules.py` | Create | `PaymentUpdateRules` — validates editability rules given NC state and requested fields |
| `src/domain/services/can_activate_payment.py` | Create | `CanActivatePaymentService` — checks `Claim.active` before reactivation |
| `src/application/use_cases/payments/actualizar_pago.py` | Create | `ActualizarPago` — delegates to `PaymentUpdateRules`, then updates |
| `src/application/use_cases/payments/activar_pago.py` | Create | `ActivarPago` — delegates to `CanActivatePaymentService`, then activates |
| `src/infrastructure/container.py` | Modify | Import and wire domain services + new use cases as properties |
| `tests/test_payments.py` | Modify | Add fixtures and test scenarios for both domain services and use cases |

## Interfaces / Contracts

### Entity change

```python
# Before
amount: float = Field(0, ge=0)

# After
amount: float = Field(gt=0)  # no default — must be provided and > 0
```

### PaymentUpdateRules (domain service)

```python
class PaymentUpdateRules:
    """Validate payment editability rules."""
    def __init__(self, nc_payment_repo: NcPaymentRepoPort,
                 payment_via_repo: PaymentViaRepoPort) -> None: ...

    def validate(
        self,
        payment_id: UUID,
        input_data: ActualizarPagoInput,
    ) -> None:
        """Raise ValueError if any editability rule is violated."""
```

### CanActivatePaymentService (domain service)

```python
class CanActivatePaymentService:
    """Check if a payment can be reactivated based on claim state."""
    def __init__(self, claim_repo: ClaimRepoPort) -> None: ...

    def execute(self, payment: Payment) -> tuple[bool, str]:
        """Return (can_activate, reason)."""
```

### ActualizarPago (use case)

```python
class ActualizarPagoInput(BaseModel):
    payment_id: UUID
    payer_id: UUID | None = None
    payment_via_id: UUID | None = None
    payee_id: UUID | None = None
    amount: float | None = None

class ActualizarPagoOutput(BaseModel):
    success: bool

class ActualizarPago:
    def __init__(
        self,
        payment_repo: PaymentRepoPort,
        update_rules: PaymentUpdateRules,
    ) -> None: ...
    def execute(self, input_data: ActualizarPagoInput) -> ActualizarPagoOutput: ...
```

### ActivarPago (use case)

```python
class ActivarPagoInput(BaseModel):
    payment_id: UUID

class ActivarPagoOutput(BaseModel):
    payment_id: UUID
    success: bool
    reason: str = ""

class ActivarPago:
    def __init__(
        self,
        payment_repo: PaymentRepoPort,
        can_activate_svc: CanActivatePaymentService,
    ) -> None: ...
    def execute(self, input_data: ActivarPagoInput) -> ActivarPagoOutput: ...
```

## Testing Strategy

| Layer | What | Approach |
|-------|------|----------|
| Entity | `Payment(amount=0)` | `pytest.raises(ValidationError)` — Pydantic catches it |
| Domain | `PaymentUpdateRules` — change to NC via (no NC exists) | `pytest.raises(ValueError)` |
| Domain | `PaymentUpdateRules` — has NC, non-amount field changed | `pytest.raises(ValueError)` |
| Domain | `PaymentUpdateRules` — has NC, only amount changed | Happy path → no error |
| Domain | `CanActivatePaymentService` — claim active | Returns `(True, ...)` |
| Domain | `CanActivatePaymentService` — claim inactive | Returns `(False, ...)` |
| UC | `ActualizarPago` — full happy path (no NC) | `success=True`, repo updated |
| UC | `ActualizarPago` — non-existent payment | `success=False` |
| UC | `ActivarPago` — full happy path | `success=True`, payment activated |
| UC | `ActivarPago` — payment not found | `success=False` |

All tests use existing in-memory repositories.

## Migration / Rollout

No migration required. All changes are additive except the `Payment.amount` constraint change, which only affects new Payment objects (no schema change).

## Open Questions

None.
