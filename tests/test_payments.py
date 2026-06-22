"""Unit tests for payment domain service and use cases (Phases 3 & 4)."""

from typing import Any
from uuid import UUID, uuid4

import pytest
from pydantic import ValidationError

from src.adapters.persistence.inmemory_claim_repository import (
    InMemoryClaimRepository,
)
from src.adapters.persistence.inmemory_ncpayment_repository import (
    InMemoryNcPaymentRepository,
)
from src.adapters.persistence.inmemory_payment_repository import (
    InMemoryPaymentRepository,
)
from src.domain.models.entities import (
    Agent,
    Claim,
    CreditNote,
    Invoice,
    Payment,
    PaymentVia,
)
from src.domain.exceptions import (
    ClaimHasActivePaymentsError,
    InvalidNCConfigurationError,
    InvalidPaymentUpdateError,
)
from src.domain.services.can_activate_payment import CanActivatePaymentService
from src.domain.services.can_inactivate_payment import CanInactivatePaymentService
from src.domain.services.payment_update_rules import PaymentUpdateRules
from src.application.use_cases.payments.activar_pago import (
    ActivarPago,
    ActivarPagoInput,
)
from src.application.use_cases.payments.actualizar_pago import (
    ActualizarPago,
    ActualizarPagoInput,
)
from src.application.use_cases.payments.registrar_pago import (
    RegistrarPago,
    RegistrarPagoInput,
)
from src.application.use_cases.payments.inactivar_pago import (
    InactivarPago,
    InactivarPagoInput,
)
from src.application.use_cases.payments.obtener_pagos import ObtenerPagos
from src.application.use_cases.payments.registrar_nc import (
    RegistrarNotaCredito,
    RegistrarNotaCreditoInput,
)
from src.application.use_cases.payments.obtener_ncs import ObtenerNotasCredito
from src.application.use_cases.payments.marcar_nc_entregada import (
    MarcarNotaCreditoEntregada,
    MarcarNotaCreditoEntregadaInput,
)



# ═══════════════════════════════════════════════════════════════════════════════
# Stub repositories
# ═══════════════════════════════════════════════════════════════════════════════


class InMemoryBillingRepository:
    """Minimal in-memory BillingRepoPort stub for testing.

    Implements only the methods used by CanInactivatePaymentService.
    """

    def __init__(self) -> None:
        self._store: list[Invoice] = []

    # ── BaseRepo[Invoice] ─────────────────────────────────────────────────────

    def add(self, model: Invoice) -> Invoice:
        self._store.append(model)
        return model

    def get_by_id(self, id: UUID) -> Invoice | None:
        return next((i for i in self._store if i.invoice_id == id), None)

    def get_all(self) -> list[Invoice]:
        return list(self._store)

    def delete(self, id: UUID) -> None:
        self._store = [i for i in self._store if i.invoice_id != id]

    def update(self, id: UUID, model: Invoice) -> bool:
        for idx, inv in enumerate(self._store):
            if inv.invoice_id == id:
                self._store[idx] = model
                return True
        return False

    def exists(self, data: dict[str, Any]) -> bool:
        return any(
            all(getattr(i, k) == v for k, v in data.items()) for i in self._store
        )

    def get_by_ids(self, ids: list[UUID]) -> list[Invoice]:
        return [i for i in self._store if i.invoice_id in ids]

    # ── _DocReachable[Invoice] ────────────────────────────────────────────────

    def get_by_document_id(self, document_id: UUID) -> list[Invoice]:
        return []

    def get_by_document(self, document: bytes) -> list[Invoice]:
        return []

    # ── BillingRepoPort custom ────────────────────────────────────────────────

    def get_by_period_id(self, period_id: UUID) -> list[Invoice]:
        return [i for i in self._store if i.period_id == period_id]


class InMemoryAgentRepository:
    """Minimal in-memory AgentRepoPort stub for testing."""

    def __init__(self) -> None:
        self._store: list[Agent] = []

    def add(self, model: Agent) -> Agent:
        self._store.append(model)
        return model

    def get_by_id(self, id: UUID) -> Agent | None:
        return next((a for a in self._store if a.agent_id == id), None)

    def get_all(self) -> list[Agent]:
        return list(self._store)

    def delete(self, id: UUID) -> None:
        self._store = [a for a in self._store if a.agent_id != id]

    def update(self, id: UUID, model: Agent) -> bool:
        for idx, a in enumerate(self._store):
            if a.agent_id == id:
                self._store[idx] = model
                return True
        return False

    def exists(self, data: dict[str, Any]) -> bool:
        return any(
            all(getattr(a, k) == v for k, v in data.items()) for a in self._store
        )

    def get_by_ids(self, ids: list[UUID]) -> list[Agent]:
        return [a for a in self._store if a.agent_id in ids]

    def activate(self, id: UUID) -> bool:
        agent = self.get_by_id(id)
        if agent:
            return self.update(id, agent.model_copy(update={"active": True}))
        return False

    def inactivate(self, id: UUID) -> bool:
        agent = self.get_by_id(id)
        if agent:
            return self.update(id, agent.model_copy(update={"active": False}))
        return False

    def get_by_name(self, name: str) -> Agent | None:
        return next((a for a in self._store if a.name == name), None)

    def get_sm(self) -> Agent | None:
        return self.get_by_name("SM")

    def get_prestador(self) -> Agent | None:
        return self.get_by_name("PRESTADOR")

    def get_sos(self) -> Agent | None:
        return self.get_by_name("SOS")

    def get_asegurado(self) -> Agent | None:
        return self.get_by_name("ASEGURADO")


class InMemoryPaymentViaRepository:
    """Minimal in-memory PaymentViaRepoPort stub for testing."""

    def __init__(self) -> None:
        self._store: list[PaymentVia] = []

    def add(self, model: PaymentVia) -> PaymentVia:
        self._store.append(model)
        return model

    def get_by_id(self, id: UUID) -> PaymentVia | None:
        return next((p for p in self._store if p.payment_via_id == id), None)

    def get_all(self) -> list[PaymentVia]:
        return list(self._store)

    def delete(self, id: UUID) -> None:
        self._store = [p for p in self._store if p.payment_via_id != id]

    def update(self, id: UUID, model: PaymentVia) -> bool:
        for idx, p in enumerate(self._store):
            if p.payment_via_id == id:
                self._store[idx] = model
                return True
        return False

    def exists(self, data: dict[str, Any]) -> bool:
        return any(
            all(getattr(p, k) == v for k, v in data.items()) for p in self._store
        )

    def get_by_ids(self, ids: list[UUID]) -> list[PaymentVia]:
        return [p for p in self._store if p.payment_via_id in ids]

    def activate(self, id: UUID) -> bool:
        via = self.get_by_id(id)
        if via:
            return self.update(id, via.model_copy(update={"active": True}))
        return False

    def inactivate(self, id: UUID) -> bool:
        via = self.get_by_id(id)
        if via:
            return self.update(id, via.model_copy(update={"active": False}))
        return False

    def get_by_name(self, name: str) -> PaymentVia | None:
        return next((p for p in self._store if p.name == name), None)

    def get_transferencia(self) -> PaymentVia | None:
        return self.get_by_name("TRANSFERENCIA")

    def get_nc(self) -> PaymentVia | None:
        return self.get_by_name("NC")


# ═══════════════════════════════════════════════════════════════════════════════
# Fixtures
# ═══════════════════════════════════════════════════════════════════════════════


@pytest.fixture
def payment_repo() -> InMemoryPaymentRepository:
    return InMemoryPaymentRepository()


@pytest.fixture
def nc_payment_repo() -> InMemoryNcPaymentRepository:
    return InMemoryNcPaymentRepository()


@pytest.fixture
def billing_repo() -> InMemoryBillingRepository:
    return InMemoryBillingRepository()


@pytest.fixture
def agent_repo() -> InMemoryAgentRepository:
    return InMemoryAgentRepository()


@pytest.fixture
def payment_via_repo() -> InMemoryPaymentViaRepository:
    return InMemoryPaymentViaRepository()


# ── Domain service: CanInactivatePaymentService ──────────────────────────────


@pytest.fixture
def can_inactivate_svc(
    nc_payment_repo: InMemoryNcPaymentRepository,
    billing_repo: InMemoryBillingRepository,
) -> CanInactivatePaymentService:
    return CanInactivatePaymentService(nc_payment_repo, billing_repo)


# ── Use cases ────────────────────────────────────────────────────────────────


@pytest.fixture
def registrar_pago(
    payment_repo: InMemoryPaymentRepository,
    nc_payment_repo: InMemoryNcPaymentRepository,
    payment_via_repo: InMemoryPaymentViaRepository,
    agent_repo: InMemoryAgentRepository,
) -> RegistrarPago:
    return RegistrarPago(payment_repo, nc_payment_repo, payment_via_repo, agent_repo)


@pytest.fixture
def inactivar_pago(
    payment_repo: InMemoryPaymentRepository,
    can_inactivate_svc: CanInactivatePaymentService,
) -> InactivarPago:
    return InactivarPago(payment_repo, can_inactivate_svc)


@pytest.fixture
def obtener_pagos(
    payment_repo: InMemoryPaymentRepository,
) -> ObtenerPagos:
    return ObtenerPagos(payment_repo)


# ── NcPayment use cases ─────────────────────────────────────────────────────


@pytest.fixture
def registrar_nc(
    nc_payment_repo: InMemoryNcPaymentRepository,
) -> RegistrarNotaCredito:
    return RegistrarNotaCredito(nc_payment_repo)


@pytest.fixture
def obtener_ncs(
    nc_payment_repo: InMemoryNcPaymentRepository,
) -> ObtenerNotasCredito:
    return ObtenerNotasCredito(nc_payment_repo)


@pytest.fixture
def marcar_nc_entregada(
    nc_payment_repo: InMemoryNcPaymentRepository,
) -> MarcarNotaCreditoEntregada:
    return MarcarNotaCreditoEntregada(nc_payment_repo)


def _credit_note(**overrides: Any) -> CreditNote:
    """Create a CreditNote with sensible defaults."""
    defaults: dict[str, Any] = {
        "nc_payment_id": uuid4(),
        "payment_id": uuid4(),
        "period_id": None,
        "delivered": False,
    }
    return CreditNote(**{**defaults, **overrides})


# ═══════════════════════════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════════════════════════


def _payment(**overrides: Any) -> Payment:
    """Create a Payment with sensible defaults."""
    defaults: dict[str, Any] = {
        "payment_id": uuid4(),
        "claim_id": uuid4(),
        "payer_id": uuid4(),
        "payee_id": uuid4(),
        "payment_via_id": uuid4(),
        "amount": 1000.0,
        "active": True,
    }
    return Payment(**{**defaults, **overrides})


def _invoice(**overrides: Any) -> Invoice:
    """Create an Invoice with sensible defaults."""
    defaults: dict[str, Any] = {
        "invoice_id": uuid4(),
        "invoice_number": "F001",
        "period_id": uuid4(),
        "emited_date": "2026-01-15T00:00:00",
        "amount": 5000.0,
    }
    return Invoice(**{**defaults, **overrides})


def _seed_agents(agent_repo: InMemoryAgentRepository) -> dict[str, Agent]:
    """Seed SOS and SM agents, return them by name."""
    sos = Agent(agent_id=uuid4(), name="SOS")
    sm = Agent(agent_id=uuid4(), name="SM")
    agent_repo.add(sos)
    agent_repo.add(sm)
    return {"SOS": sos, "SM": sm}


def _seed_nc_via(
    payment_via_repo: InMemoryPaymentViaRepository,
) -> PaymentVia:
    """Seed and return the NC PaymentVia."""
    nc = PaymentVia(payment_via_id=uuid4(), name="NC")
    payment_via_repo.add(nc)
    return nc


# ═══════════════════════════════════════════════════════════════════════════════
# Phase 3 — CanInactivatePaymentService
# ═══════════════════════════════════════════════════════════════════════════════


def test_can_inactivate_no_nc_payment(
    can_inactivate_svc: CanInactivatePaymentService,
    payment_repo: InMemoryPaymentRepository,
) -> None:
    """Scenario: payment has no associated NcPayment → can inactivate."""
    payment = _payment()
    payment_repo.add(payment)

    can, reason = can_inactivate_svc.execute(payment.payment_id)

    assert can is True
    assert "No credit note associated" in reason


def test_can_inactivate_nc_no_invoice(
    can_inactivate_svc: CanInactivatePaymentService,
    payment_repo: InMemoryPaymentRepository,
    nc_payment_repo: InMemoryNcPaymentRepository,
) -> None:
    """Scenario: NcPayment exists but period has no invoices → can inactivate."""
    payment = _payment()
    payment_repo.add(payment)
    period_id = uuid4()
    nc_payment_repo.add(
        CreditNote(
            nc_payment_id=uuid4(),
            payment_id=payment.payment_id,
            period_id=period_id,
        )
    )

    can, reason = can_inactivate_svc.execute(payment.payment_id)

    assert can is True
    assert "no invoices" in reason


def test_can_inactivate_period_closed(
    can_inactivate_svc: CanInactivatePaymentService,
    payment_repo: InMemoryPaymentRepository,
    nc_payment_repo: InMemoryNcPaymentRepository,
    billing_repo: InMemoryBillingRepository,
) -> None:
    """Scenario: NcPayment exists and period has invoices → cannot inactivate."""
    payment = _payment()
    payment_repo.add(payment)
    period_id = uuid4()
    nc_payment_repo.add(
        CreditNote(
            nc_payment_id=uuid4(),
            payment_id=payment.payment_id,
            period_id=period_id,
        )
    )
    billing_repo.add(_invoice(period_id=period_id))

    can, reason = can_inactivate_svc.execute(payment.payment_id)

    assert can is False
    assert "closed period" in reason


# ═══════════════════════════════════════════════════════════════════════════════
# Phase 4.1 — RegistrarPago
# ═══════════════════════════════════════════════════════════════════════════════


def test_registrar_pago_transferencia_happy(
    registrar_pago: RegistrarPago,
    payment_repo: InMemoryPaymentRepository,
    payment_via_repo: InMemoryPaymentViaRepository,
) -> None:
    """Happy path: transferencia (not NC) creates a payment successfully."""
    transferencia = PaymentVia(payment_via_id=uuid4(), name="TRANSFERENCIA")
    payment_via_repo.add(transferencia)

    result = registrar_pago.execute(
        RegistrarPagoInput(
            claim_id=uuid4(),
            payer_id=uuid4(),
            payee_id=uuid4(),
            payment_via_id=transferencia.payment_via_id,
            amount=2500.0,
        )
    )

    assert result.payment_id is not None
    assert result.success is True
    # Verify it was persisted
    stored = payment_repo.get_by_id(result.payment_id)
    assert stored is not None
    assert stored.amount == 2500.0
    assert stored.active is True


def test_registrar_pago_nc_valid(
    registrar_pago: RegistrarPago,
    payment_repo: InMemoryPaymentRepository,
    nc_payment_repo: InMemoryNcPaymentRepository,
    payment_via_repo: InMemoryPaymentViaRepository,
    agent_repo: InMemoryAgentRepository,
) -> None:
    """NC payment with correct payer=SOS and payee=SM creates payment + NC."""
    agents = _seed_agents(agent_repo)
    nc_via = _seed_nc_via(payment_via_repo)
    period_id = uuid4()
    claim_id = uuid4()

    result = registrar_pago.execute(
        RegistrarPagoInput(
            claim_id=claim_id,
            payer_id=agents["SOS"].agent_id,
            payee_id=agents["SM"].agent_id,
            payment_via_id=nc_via.payment_via_id,
            amount=3000.0,
            period_id=period_id,
        )
    )

    assert result.success is True
    stored = payment_repo.get_by_id(result.payment_id)
    assert stored is not None
    assert stored.amount == 3000.0
    # NcPayment should have been created
    nc = nc_payment_repo.get_by_payment_id(result.payment_id)
    assert nc is not None
    assert nc.period_id == period_id


def test_registrar_pago_nc_wrong_payer(
    registrar_pago: RegistrarPago,
    payment_via_repo: InMemoryPaymentViaRepository,
    agent_repo: InMemoryAgentRepository,
) -> None:
    """NC payment with wrong payer raises ValueError."""
    agents = _seed_agents(agent_repo)
    nc_via = _seed_nc_via(payment_via_repo)
    wrong_payer_id = uuid4()

    with pytest.raises(InvalidNCConfigurationError, match="payer"):
        registrar_pago.execute(
            RegistrarPagoInput(
                claim_id=uuid4(),
                payer_id=wrong_payer_id,
                payee_id=agents["SM"].agent_id,
                payment_via_id=nc_via.payment_via_id,
                amount=3000.0,
            )
        )


def test_registrar_pago_nc_wrong_payee(
    registrar_pago: RegistrarPago,
    payment_via_repo: InMemoryPaymentViaRepository,
    agent_repo: InMemoryAgentRepository,
) -> None:
    """NC payment with wrong payee raises ValueError."""
    agents = _seed_agents(agent_repo)
    nc_via = _seed_nc_via(payment_via_repo)
    wrong_payee_id = uuid4()

    with pytest.raises(InvalidNCConfigurationError, match="payee"):
        registrar_pago.execute(
            RegistrarPagoInput(
                claim_id=uuid4(),
                payer_id=agents["SOS"].agent_id,
                payee_id=wrong_payee_id,
                payment_via_id=nc_via.payment_via_id,
                amount=3000.0,
            )
        )


# ═══════════════════════════════════════════════════════════════════════════════
# Phase 4.2 — ObtenerPagos
# ═══════════════════════════════════════════════════════════════════════════════


def test_obtener_pagos_get_by_id_found(
    obtener_pagos: ObtenerPagos,
    payment_repo: InMemoryPaymentRepository,
) -> None:
    """get_by_id returns the payment when it exists."""
    payment = _payment()
    payment_repo.add(payment)

    result = obtener_pagos.get_by_id(payment.payment_id)

    assert result is not None
    assert result.payment_id == payment.payment_id
    assert result.amount == payment.amount


def test_obtener_pagos_get_by_id_not_found(
    obtener_pagos: ObtenerPagos,
) -> None:
    """get_by_id returns None when payment does not exist."""
    result = obtener_pagos.get_by_id(uuid4())
    assert result is None


def test_obtener_pagos_get_all(
    obtener_pagos: ObtenerPagos,
    payment_repo: InMemoryPaymentRepository,
) -> None:
    """get_all returns all payments."""
    p1 = _payment()
    p2 = _payment()
    payment_repo.add(p1)
    payment_repo.add(p2)

    result = obtener_pagos.get_all()

    assert len(result) == 2
    assert {r.payment_id for r in result} == {p1.payment_id, p2.payment_id}


def test_obtener_pagos_get_by_claim_id(
    obtener_pagos: ObtenerPagos,
    payment_repo: InMemoryPaymentRepository,
) -> None:
    """get_by_claim_id returns payments for the given claim."""
    claim_id = uuid4()
    p1 = _payment(claim_id=claim_id)
    p2 = _payment(claim_id=claim_id)
    p3 = _payment(claim_id=uuid4())  # different claim
    for p in [p1, p2, p3]:
        payment_repo.add(p)

    result = obtener_pagos.get_by_claim_id(claim_id)

    assert len(result) == 2
    assert all(r.claim_id == claim_id for r in result)


# ═══════════════════════════════════════════════════════════════════════════════
# Phase 4.3 — InactivarPago
# ═══════════════════════════════════════════════════════════════════════════════


def test_inactivar_pago_success(
    inactivar_pago: InactivarPago,
    payment_repo: InMemoryPaymentRepository,
) -> None:
    """Happy path: inactive an existing payment that has no NC."""
    payment = _payment(active=True)
    payment_repo.add(payment)

    result = inactivar_pago.execute(InactivarPagoInput(payment_id=payment.payment_id))

    assert result.payment_id == payment.payment_id
    assert result.success is True
    # Verify inactivated
    stored = payment_repo.get_by_id(payment.payment_id)
    assert stored is not None
    assert stored.active is False


def test_inactivar_pago_blocked_by_closed_period(
    inactivar_pago: InactivarPago,
    payment_repo: InMemoryPaymentRepository,
    nc_payment_repo: InMemoryNcPaymentRepository,
    billing_repo: InMemoryBillingRepository,
) -> None:
    """Blocked: payment has NC linked to a period with invoices."""
    payment = _payment(active=True)
    payment_repo.add(payment)
    period_id = uuid4()
    nc_payment_repo.add(
        CreditNote(
            nc_payment_id=uuid4(),
            payment_id=payment.payment_id,
            period_id=period_id,
        )
    )
    billing_repo.add(_invoice(period_id=period_id))

    result = inactivar_pago.execute(InactivarPagoInput(payment_id=payment.payment_id))

    assert result.payment_id == payment.payment_id
    assert result.success is False
    assert "closed period" in result.reason
    # Payment should still be active
    stored = payment_repo.get_by_id(payment.payment_id)
    assert stored is not None
    assert stored.active is True


def test_inactivar_pago_not_found(
    inactivar_pago: InactivarPago,
) -> None:
    """Not found: returns success=False with reason."""
    result = inactivar_pago.execute(InactivarPagoInput(payment_id=uuid4()))

    assert result.success is False
    assert "not found" in result.reason


# ═══════════════════════════════════════════════════════════════════════════════
# Phase 4.4 — Claim deletion guard
# ═══════════════════════════════════════════════════════════════════════════════


def test_delete_claim_with_active_payments_raises(
    payment_repo: InMemoryPaymentRepository,
) -> None:
    """Guard: claim with active payments raises ValueError."""
    from src.adapters.persistence.inmemory_claim_repository import (
        InMemoryClaimRepository,
    )
    from src.application.use_cases.claims.eliminar_gestion_sos import (
        EliminarGestionSOS,
        EliminarGestionSOSInput,
    )
    from src.domain.models.entities import Claim

    claim_repo = InMemoryClaimRepository()
    claim_id = uuid4()
    claim_repo.add(
        Claim(
            claim_id=claim_id,
            claim_kind_id=uuid4(),
            group_id=uuid4(),
            claimer_name="Test",
            policy_number="POL-001",
            plate="ABC-123",
        )
    )
    # Seed an active payment for this claim
    payment_repo.add(_payment(claim_id=claim_id, active=True))
    use_case = EliminarGestionSOS(claim_repo, payment_repo)

    with pytest.raises(ClaimHasActivePaymentsError, match="active payments"):
        use_case.execute(EliminarGestionSOSInput(claim_id=claim_id))


def test_delete_claim_with_inactive_payments_succeeds(
    payment_repo: InMemoryPaymentRepository,
) -> None:
    """Guard: claim with only inactive payments proceeds normally."""
    from src.adapters.persistence.inmemory_claim_repository import (
        InMemoryClaimRepository,
    )
    from src.application.use_cases.claims.eliminar_gestion_sos import (
        EliminarGestionSOS,
        EliminarGestionSOSInput,
    )
    from src.domain.models.entities import Claim

    claim_repo = InMemoryClaimRepository()
    claim_id = uuid4()
    claim_repo.add(
        Claim(
            claim_id=claim_id,
            claim_kind_id=uuid4(),
            group_id=uuid4(),
            claimer_name="Test",
            policy_number="POL-001",
            plate="ABC-123",
        )
    )
    # Seed an inactive payment — should not block
    payment_repo.add(_payment(claim_id=claim_id, active=False))
    use_case = EliminarGestionSOS(claim_repo, payment_repo)

    result = use_case.execute(EliminarGestionSOSInput(claim_id=claim_id))

    assert result.success is True
    # Verify claim was inactivated
    stored_claim = claim_repo.get_by_id(claim_id)
    assert stored_claim is not None
    assert stored_claim.active is False


# ═══════════════════════════════════════════════════════════════════════════════
# Phase 5 — NcPayment Use Cases
# ═══════════════════════════════════════════════════════════════════════════════


def test_registrar_nc_creates_credit_note(
    registrar_nc: RegistrarNotaCredito,
    nc_payment_repo: InMemoryNcPaymentRepository,
) -> None:
    """Happy path: creates an NcPayment for a given payment and period."""
    payment_id = uuid4()
    period_id = uuid4()

    result = registrar_nc.execute(
        RegistrarNotaCreditoInput(
            payment_id=payment_id,
            period_id=period_id,
        )
    )

    assert result.success is True
    assert result.nc_payment_id is not None
    # Verify it was persisted in the repo
    stored = nc_payment_repo.get_by_id(result.nc_payment_id)
    assert stored is not None
    assert stored.payment_id == payment_id
    assert stored.period_id == period_id
    assert stored.delivered is False


def test_obtener_ncs_get_by_id_found(
    obtener_ncs: ObtenerNotasCredito,
    nc_payment_repo: InMemoryNcPaymentRepository,
) -> None:
    """get_by_id returns the NC when it exists."""
    nc = _credit_note()
    nc_payment_repo.add(nc)

    result = obtener_ncs.get_by_id(nc.nc_payment_id)

    assert result is not None
    assert result.nc_payment_id == nc.nc_payment_id
    assert result.payment_id == nc.payment_id


def test_obtener_ncs_get_by_id_not_found(
    obtener_ncs: ObtenerNotasCredito,
) -> None:
    """get_by_id returns None when NC does not exist."""
    result = obtener_ncs.get_by_id(uuid4())
    assert result is None


def test_obtener_ncs_get_all(
    obtener_ncs: ObtenerNotasCredito,
    nc_payment_repo: InMemoryNcPaymentRepository,
) -> None:
    """get_all returns all credit notes."""
    nc1 = _credit_note()
    nc2 = _credit_note()
    nc_payment_repo.add(nc1)
    nc_payment_repo.add(nc2)

    result = obtener_ncs.get_all()

    assert len(result) == 2
    assert {r.nc_payment_id for r in result} == {nc1.nc_payment_id, nc2.nc_payment_id}


def test_obtener_ncs_get_by_payment_id_found(
    obtener_ncs: ObtenerNotasCredito,
    nc_payment_repo: InMemoryNcPaymentRepository,
) -> None:
    """get_by_payment_id returns the NC for the given payment."""
    payment_id = uuid4()
    nc = _credit_note(payment_id=payment_id)
    nc_payment_repo.add(nc)

    result = obtener_ncs.get_by_payment_id(payment_id)

    assert result is not None
    assert result.nc_payment_id == nc.nc_payment_id


def test_obtener_ncs_get_by_payment_id_not_found(
    obtener_ncs: ObtenerNotasCredito,
) -> None:
    """get_by_payment_id returns None when no NC for that payment."""
    result = obtener_ncs.get_by_payment_id(uuid4())
    assert result is None


def test_obtener_ncs_get_by_period_id(
    obtener_ncs: ObtenerNotasCredito,
    nc_payment_repo: InMemoryNcPaymentRepository,
) -> None:
    """get_by_period_id returns all NCs for the given period."""
    period_id = uuid4()
    nc1 = _credit_note(period_id=period_id)
    nc2 = _credit_note(period_id=period_id)
    nc3 = _credit_note(period_id=uuid4())  # different period
    for nc in [nc1, nc2, nc3]:
        nc_payment_repo.add(nc)

    result = obtener_ncs.get_by_period_id(period_id)

    assert len(result) == 2
    assert all(r.period_id == period_id for r in result)


def test_marcar_nc_entregada_success(
    marcar_nc_entregada: MarcarNotaCreditoEntregada,
    nc_payment_repo: InMemoryNcPaymentRepository,
) -> None:
    """Happy path: mark an existing NC as delivered."""
    nc = _credit_note(delivered=False)
    nc_payment_repo.add(nc)

    result = marcar_nc_entregada.execute(
        MarcarNotaCreditoEntregadaInput(nc_payment_id=nc.nc_payment_id)
    )

    assert result.success is True
    # Verify it was updated
    stored = nc_payment_repo.get_by_id(nc.nc_payment_id)
    assert stored is not None
    assert stored.delivered is True


def test_marcar_nc_entregada_not_found(
    marcar_nc_entregada: MarcarNotaCreditoEntregada,
) -> None:
    """Not found: returns success=False."""
    result = marcar_nc_entregada.execute(
        MarcarNotaCreditoEntregadaInput(nc_payment_id=uuid4())
    )
    assert result.success is False


# ═══════════════════════════════════════════════════════════════════════════════
# Phase 6 — PaymentUpdateRules (domain service)
# ═══════════════════════════════════════════════════════════════════════════════


@pytest.fixture
def claim_repo() -> InMemoryClaimRepository:
    return InMemoryClaimRepository()


@pytest.fixture
def payment_update_rules(
    nc_payment_repo: InMemoryNcPaymentRepository,
    payment_via_repo: InMemoryPaymentViaRepository,
) -> PaymentUpdateRules:
    return PaymentUpdateRules(nc_payment_repo, payment_via_repo)


@pytest.fixture
def can_activate_svc(
    claim_repo: InMemoryClaimRepository,
) -> CanActivatePaymentService:
    return CanActivatePaymentService(claim_repo)


@pytest.fixture
def actualizar_pago(
    payment_repo: InMemoryPaymentRepository,
    payment_update_rules: PaymentUpdateRules,
) -> ActualizarPago:
    return ActualizarPago(payment_repo, payment_update_rules)


@pytest.fixture
def activar_pago(
    payment_repo: InMemoryPaymentRepository,
    can_activate_svc: CanActivatePaymentService,
) -> ActivarPago:
    return ActivarPago(payment_repo, can_activate_svc)


# ── 4.1 Entity validation ────────────────────────────────────────────────────


def test_payment_amount_must_be_positive() -> None:
    """Payment(amount=0) raises Pydantic ValidationError."""
    with pytest.raises(ValidationError):
        Payment(
            payment_id=uuid4(),
            claim_id=uuid4(),
            payer_id=uuid4(),
            payee_id=uuid4(),
            payment_via_id=uuid4(),
            amount=0,
        )


# ── 4.2–4.4 PaymentUpdateRules ────────────────────────────────────────────────


def test_update_rules_rejects_change_to_nc_via_when_no_nc(
    payment_update_rules: PaymentUpdateRules,
    payment_repo: InMemoryPaymentRepository,
    payment_via_repo: InMemoryPaymentViaRepository,
) -> None:
    """No NC exists → changing to NC via raises ValueError."""
    payment = _payment()
    payment_repo.add(payment)
    nc_via = _seed_nc_via(payment_via_repo)

    with pytest.raises(InvalidPaymentUpdateError, match="Credit Note"):
        payment_update_rules.validate(
            payment_id=payment.payment_id,
            payment_via_id=nc_via.payment_via_id,
        )


def test_update_rules_rejects_non_amount_field_when_nc_exists(
    payment_update_rules: PaymentUpdateRules,
    payment_repo: InMemoryPaymentRepository,
    nc_payment_repo: InMemoryNcPaymentRepository,
    payment_via_repo: InMemoryPaymentViaRepository,
) -> None:
    """NC exists → changing a non-amount field raises ValueError."""
    payment = _payment()
    payment_repo.add(payment)
    nc_payment_repo.add(
        CreditNote(
            nc_payment_id=uuid4(),
            payment_id=payment.payment_id,
            period_id=uuid4(),
        )
    )

    with pytest.raises(InvalidPaymentUpdateError, match="Only amount"):
        payment_update_rules.validate(
            payment_id=payment.payment_id,
            payer_id=uuid4(),
        )


def test_update_rules_allows_amount_only_when_nc_exists(
    payment_update_rules: PaymentUpdateRules,
    payment_repo: InMemoryPaymentRepository,
    nc_payment_repo: InMemoryNcPaymentRepository,
) -> None:
    """NC exists → changing only amount is allowed (no error)."""
    payment = _payment(amount=1000.0)
    payment_repo.add(payment)
    nc_payment_repo.add(
        CreditNote(
            nc_payment_id=uuid4(),
            payment_id=payment.payment_id,
            period_id=uuid4(),
        )
    )

    # Should not raise
    payment_update_rules.validate(
        payment_id=payment.payment_id,
        amount=2000.0,
    )


# ── 4.5–4.6 CanActivatePaymentService ─────────────────────────────────────────


def test_can_activate_claim_active(
    can_activate_svc: CanActivatePaymentService,
    claim_repo: InMemoryClaimRepository,
) -> None:
    """Returns (True, ...) when the claim is active."""
    claim = Claim(
        claim_id=uuid4(),
        claim_kind_id=uuid4(),
        group_id=uuid4(),
        claimer_name="Test",
        policy_number="POL-001",
        plate="ABC-123",
        active=True,
    )
    claim_repo.add(claim)
    payment = _payment(claim_id=claim.claim_id)

    can, reason = can_activate_svc.execute(payment)

    assert can is True
    assert "active" in reason


def test_can_activate_claim_inactive(
    can_activate_svc: CanActivatePaymentService,
    claim_repo: InMemoryClaimRepository,
) -> None:
    """Returns (False, ...) when the claim is inactive."""
    claim = Claim(
        claim_id=uuid4(),
        claim_kind_id=uuid4(),
        group_id=uuid4(),
        claimer_name="Test",
        policy_number="POL-001",
        plate="ABC-123",
        active=False,
    )
    claim_repo.add(claim)
    payment = _payment(claim_id=claim.claim_id)

    can, reason = can_activate_svc.execute(payment)

    assert can is False
    assert "not active" in reason


# ── 4.7–4.8 ActualizarPago ────────────────────────────────────────────────────


def test_actualizar_pago_happy(
    actualizar_pago: ActualizarPago,
    payment_repo: InMemoryPaymentRepository,
) -> None:
    """Happy path: update amount, success=True, repo updated."""
    payment = _payment(amount=1000.0)
    payment_repo.add(payment)

    result = actualizar_pago.execute(
        ActualizarPagoInput(
            payment_id=payment.payment_id,
            amount=2500.0,
        )
    )

    assert result.success is True
    stored = payment_repo.get_by_id(payment.payment_id)
    assert stored is not None
    assert stored.amount == 2500.0


def test_actualizar_pago_not_found(
    actualizar_pago: ActualizarPago,
) -> None:
    """Non-existent payment → success=False."""
    result = actualizar_pago.execute(ActualizarPagoInput(payment_id=uuid4()))
    assert result.success is False


# ── 4.9–4.10 ActivarPago ──────────────────────────────────────────────────────


def test_activar_pago_happy(
    activar_pago: ActivarPago,
    payment_repo: InMemoryPaymentRepository,
    claim_repo: InMemoryClaimRepository,
) -> None:
    """Happy path: activate an inactive payment with active claim."""
    claim = Claim(
        claim_id=uuid4(),
        claim_kind_id=uuid4(),
        group_id=uuid4(),
        claimer_name="Test",
        policy_number="POL-001",
        plate="ABC-123",
        active=True,
    )
    claim_repo.add(claim)
    payment = _payment(claim_id=claim.claim_id, active=False)
    payment_repo.add(payment)

    result = activar_pago.execute(ActivarPagoInput(payment_id=payment.payment_id))

    assert result.success is True
    assert result.payment_id == payment.payment_id
    stored = payment_repo.get_by_id(payment.payment_id)
    assert stored is not None
    assert stored.active is True


def test_activar_pago_not_found(
    activar_pago: ActivarPago,
) -> None:
    """Non-existent payment → success=False."""
    result = activar_pago.execute(ActivarPagoInput(payment_id=uuid4()))

    assert result.success is False
    assert "not found" in result.reason
