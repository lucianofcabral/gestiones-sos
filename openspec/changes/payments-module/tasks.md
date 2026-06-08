# Tasks: payments-module

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | 1000–1200 |
| 400-line budget risk | High |
| Chained PRs recommended | Yes |
| Suggested split | PR 1: Foundation + Repos → PR 2: Domain Service + Payment UCs + Guard → PR 3: NcPayment UCs + Wiring |
| Delivery strategy | ask-on-risk |
| Chain strategy | feature-branch-chain |

Decision needed before apply: Yes → resolved: feature-branch-chain, PR 1 targets feature branch
Chained PRs recommended: Yes
Chain strategy: feature-branch-chain
400-line budget risk: High

### Suggested Work Units

| Unit | Goal | Likely PR | Notes |
|------|------|-----------|-------|
| 1 | Domain foundation + 4 repo implementations | PR 1 | ✅ COMPLETE. Entities, ports, tables, migration, repos, repo tests |
| 2 | Domain service + Payment use cases + claim guard | PR 2 | base=main. CanInactivate, Registrar/Obtener/Inactivar pago, Eliminar guard, use-case tests |
| 3 | NcPayment use cases + container wiring | PR 3 | base=main. NcPayment CRUD, container wiring, nc-payment tests |

## Phase 1: Domain Foundation

- [x] 1.1 Add `active: bool = True` to Payment and CreditNote in `entities.py`
- [x] 1.2 Add `_Activatable[Payment]` to PaymentRepoPort, `_Activatable[CreditNote]` to NcPaymentRepoPort in `repositories.py`; add `inactivatable(id)` on PaymentRepoPort, `mark_delivered(id)` on NcPaymentRepoPort, `get_by_period_id(period_id)` on BillingRepoPort
- [x] 1.3 Add `payments` and `nc_payments` tables to `tables.py` with FKs and defaults
- [x] 1.4 Create Alembic migration creating both tables

## Phase 2: Repository Implementations

- [x] 2.1 RED→GREEN→REFACTOR: Implement `InMemoryPaymentRepository` covering all PaymentRepoPort methods
- [x] 2.2 Implement `SqlAlchemyPaymentRepository` following `SqlAlchemyClaimRepository` pattern
- [x] 2.3 RED→GREEN→REFACTOR: Implement `InMemoryNcPaymentRepository` covering all NcPaymentRepoPort methods
- [x] 2.4 Implement `SqlAlchemyNcPaymentRepository` following existing SQLAlchemy pattern

## Phase 3: Domain Service

- [ ] 3.1 RED→GREEN→REFACTOR: Create `CanInactivatePaymentService` in `src/domain/services/can_inactivate_payment.py` with 3-scenario tests (no NC, NC no invoice, period closed)

## Phase 4: Payment Use Cases + Claim Guard

- [ ] 4.1 RED→GREEN→REFACTOR: Create `RegistrarPago` — Payment creation with NC validation (payer=SOS, payee=SM) via PaymentViaRepoPort + AgentRepoPort
- [ ] 4.2 RED→GREEN→REFACTOR: Create `ObtenerPagos` — get_by_id, get_all, get_by_claim_id
- [ ] 4.3 RED→GREEN→REFACTOR: Create `InactivarPago` — uses CanInactivatePaymentService, returns success + reason
- [ ] 4.4 RED→GREEN→REFACTOR: Modify `EliminarGestionSOS` — add `payment_repo` param, guard check before inactivate, update existing tests

## Phase 5: NcPayment Use Cases

- [ ] 5.1 RED→GREEN→REFACTOR: Create all NcPayment CRUD use cases (registrar, obtener, listar, actualizar, marcar_entregado, activar, inactivar) in `src/application/use_cases/payments/`

## Phase 6: Wiring

- [ ] 6.1 Wire `SqlAlchemyPaymentRepository`, `SqlAlchemyNcPaymentRepository`, `CanInactivatePaymentService` in `Container`
- [ ] 6.2 Wire `RegistrarPago`, `ObtenerPagos`, `InactivarPago` in `Container`
- [ ] 6.3 Wire all NcPayment use cases in `Container`
- [ ] 6.4 Update `EliminarGestionSOS` wiring with `payment_repo` in `Container`