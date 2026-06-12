"""Unit tests for catalog repos (Agent, PaymentVia, ClaimKind) using in-memory implementations."""

from uuid import UUID, uuid4

import pytest

from src.adapters.persistence.inmemory_agent_repository import (
    InMemoryAgentRepository,
)
from src.adapters.persistence.inmemory_payment_via_repository import (
    InMemoryPaymentViaRepository,
)
from src.adapters.persistence.inmemory_claim_kind_repository import (
    InMemoryClaimKindRepository,
)
from src.domain.models.entities import Agent, ClaimKind, PaymentVia


# ═══════════════════════════════════════════════════════════════════════════════
# Fixtures
# ═══════════════════════════════════════════════════════════════════════════════


@pytest.fixture
def agent_repo() -> InMemoryAgentRepository:
    return InMemoryAgentRepository()


@pytest.fixture
def payment_via_repo() -> InMemoryPaymentViaRepository:
    return InMemoryPaymentViaRepository()


@pytest.fixture
def claim_kind_repo() -> InMemoryClaimKindRepository:
    return InMemoryClaimKindRepository()


# ═══════════════════════════════════════════════════════════════════════════════
# Seed helpers
# ═══════════════════════════════════════════════════════════════════════════════


def _seed_agent(
    repo: InMemoryAgentRepository,
    agent_id: UUID | None = None,
    name: str = "Test Agent",
    active: bool = True,
) -> Agent:
    aid = agent_id or uuid4()
    agent = Agent(agent_id=aid, name=name, active=active)
    repo.add(agent)
    return agent


def _seed_payment_via(
    repo: InMemoryPaymentViaRepository,
    payment_via_id: UUID | None = None,
    name: str = "Test PaymentVia",
    active: bool = True,
) -> PaymentVia:
    pid = payment_via_id or uuid4()
    pv = PaymentVia(payment_via_id=pid, name=name, active=active)
    repo.add(pv)
    return pv


def _seed_claim_kind(
    repo: InMemoryClaimKindRepository,
    claim_kind_id: UUID | None = None,
    name: str = "Test ClaimKind",
    active: bool = True,
) -> ClaimKind:
    cid = claim_kind_id or uuid4()
    ck = ClaimKind(claim_kind_id=cid, name=name, active=active)
    repo.add(ck)
    return ck


# ═══════════════════════════════════════════════════════════════════════════════
# Agent Tests
# ═══════════════════════════════════════════════════════════════════════════════


class TestAgentRepo:
    """Tests for InMemoryAgentRepository — BaseRepo + AgentRepoPort + _Activatable."""

    # ── BaseRepo: get_by_id ────────────────────────────────────────────────

    def test_get_by_id_returns_agent_when_found(
        self, agent_repo: InMemoryAgentRepository
    ) -> None:
        agent = _seed_agent(agent_repo)

        result = agent_repo.get_by_id(agent.agent_id)

        assert result is not None
        assert result.agent_id == agent.agent_id
        assert result.name == agent.name

    def test_get_by_id_returns_none_when_not_found(
        self, agent_repo: InMemoryAgentRepository
    ) -> None:
        result = agent_repo.get_by_id(uuid4())
        assert result is None

    # ── BaseRepo: add ──────────────────────────────────────────────────────

    def test_add_stores_agent(self, agent_repo: InMemoryAgentRepository) -> None:
        agent = Agent(name="New Agent", agent_id=uuid4())

        result = agent_repo.add(agent)

        assert result == agent
        assert agent_repo.get_by_id(agent.agent_id) == agent

    # ── BaseRepo: get_all ──────────────────────────────────────────────────

    def test_get_all_returns_all_agents(
        self, agent_repo: InMemoryAgentRepository
    ) -> None:
        a1 = _seed_agent(agent_repo, name="Agent One")
        a2 = _seed_agent(agent_repo, name="Agent Two")

        result = agent_repo.get_all()

        assert len(result) == 2
        assert a1 in result
        assert a2 in result

    def test_get_all_returns_empty_when_no_agents(
        self, agent_repo: InMemoryAgentRepository
    ) -> None:
        result = agent_repo.get_all()
        assert result == []

    # ── BaseRepo: exists ───────────────────────────────────────────────────

    def test_exists_returns_true_when_match(
        self, agent_repo: InMemoryAgentRepository
    ) -> None:
        _seed_agent(agent_repo, name="Unique Agent")

        assert agent_repo.exists({"name": "Unique Agent"}) is True

    def test_exists_returns_false_when_no_match(
        self, agent_repo: InMemoryAgentRepository
    ) -> None:
        _seed_agent(agent_repo, name="Unique Agent")

        assert agent_repo.exists({"name": "Other Agent"}) is False

    # ── BaseRepo: update ───────────────────────────────────────────────────

    def test_update_returns_true_and_modifies(
        self, agent_repo: InMemoryAgentRepository
    ) -> None:
        agent = _seed_agent(agent_repo, name="Original")
        updated = Agent(agent_id=agent.agent_id, name="Modified")

        result = agent_repo.update(agent.agent_id, updated)

        assert result is True
        stored = agent_repo.get_by_id(agent.agent_id)
        assert stored is not None
        assert stored.name == "Modified"

    def test_update_returns_false_when_not_found(
        self, agent_repo: InMemoryAgentRepository
    ) -> None:
        a = Agent(name="Ghost")
        result = agent_repo.update(a.agent_id, a)
        assert result is False

    # ── BaseRepo: delete ───────────────────────────────────────────────────

    def test_delete_removes_agent(
        self, agent_repo: InMemoryAgentRepository
    ) -> None:
        agent = _seed_agent(agent_repo)

        agent_repo.delete(agent.agent_id)

        assert agent_repo.get_by_id(agent.agent_id) is None

    def test_delete_nonexistent_does_nothing(
        self, agent_repo: InMemoryAgentRepository
    ) -> None:
        agent_repo.delete(uuid4())  # should not raise

    # ── BaseRepo: get_by_ids ───────────────────────────────────────────────

    def test_get_by_ids_returns_matching(
        self, agent_repo: InMemoryAgentRepository
    ) -> None:
        a1 = _seed_agent(agent_repo)
        a2 = _seed_agent(agent_repo)
        a3 = _seed_agent(agent_repo)

        result = agent_repo.get_by_ids([a1.agent_id, a3.agent_id])

        assert len(result) == 2
        assert a1 in result
        assert a3 in result
        assert a2 not in result

    def test_get_by_ids_returns_empty_when_none_match(
        self, agent_repo: InMemoryAgentRepository
    ) -> None:
        _seed_agent(agent_repo)
        result = agent_repo.get_by_ids([uuid4(), uuid4()])
        assert result == []

    # ── AgentRepoPort: get_by_name ─────────────────────────────────────────

    def test_get_by_name_returns_agent_when_found(
        self, agent_repo: InMemoryAgentRepository
    ) -> None:
        _seed_agent(agent_repo, name="SOS")

        result = agent_repo.get_by_name("SOS")

        assert result is not None
        assert result.name == "SOS"

    def test_get_by_name_returns_none_when_not_found(
        self, agent_repo: InMemoryAgentRepository
    ) -> None:
        result = agent_repo.get_by_name("NonExistent")
        assert result is None

    # ── AgentRepoPort: named getters ───────────────────────────────────────

    def test_get_sos_returns_sos_agent(
        self, agent_repo: InMemoryAgentRepository
    ) -> None:
        _seed_agent(agent_repo, name="SOS")

        result = agent_repo.get_sos()

        assert result is not None
        assert result.name == "SOS"

    def test_get_sm_returns_sm_agent(
        self, agent_repo: InMemoryAgentRepository
    ) -> None:
        _seed_agent(agent_repo, name="SM")

        result = agent_repo.get_sm()

        assert result is not None
        assert result.name == "SM"

    def test_get_prestador_returns_prestador(
        self, agent_repo: InMemoryAgentRepository
    ) -> None:
        _seed_agent(agent_repo, name="Prestador")

        result = agent_repo.get_prestador()

        assert result is not None
        assert result.name == "Prestador"

    def test_get_asegurado_returns_asegurado(
        self, agent_repo: InMemoryAgentRepository
    ) -> None:
        _seed_agent(agent_repo, name="Asegurado")

        result = agent_repo.get_asegurado()

        assert result is not None
        assert result.name == "Asegurado"

    def test_named_getter_returns_none_when_not_found(
        self, agent_repo: InMemoryAgentRepository
    ) -> None:
        assert agent_repo.get_sos() is None
        assert agent_repo.get_sm() is None
        assert agent_repo.get_prestador() is None
        assert agent_repo.get_asegurado() is None

    # ── _Activatable ───────────────────────────────────────────────────────

    def test_activate_sets_active_true(
        self, agent_repo: InMemoryAgentRepository
    ) -> None:
        agent = _seed_agent(agent_repo, active=False)

        result = agent_repo.activate(agent.agent_id)

        assert result is True
        assert agent_repo.get_by_id(agent.agent_id) is not None
        assert agent_repo.get_by_id(agent.agent_id).active is True

    def test_inactivate_sets_active_false(
        self, agent_repo: InMemoryAgentRepository
    ) -> None:
        agent = _seed_agent(agent_repo, active=True)

        result = agent_repo.inactivate(agent.agent_id)

        assert result is True
        assert agent_repo.get_by_id(agent.agent_id).active is False

    def test_activate_returns_false_when_not_found(
        self, agent_repo: InMemoryAgentRepository
    ) -> None:
        assert agent_repo.activate(uuid4()) is False

    def test_inactivate_returns_false_when_not_found(
        self, agent_repo: InMemoryAgentRepository
    ) -> None:
        assert agent_repo.inactivate(uuid4()) is False


# ═══════════════════════════════════════════════════════════════════════════════
# PaymentVia Tests
# ═══════════════════════════════════════════════════════════════════════════════


class TestPaymentViaRepo:
    """Tests for InMemoryPaymentViaRepository — BaseRepo + PaymentViaRepoPort + _Activatable."""

    # ── BaseRepo: get_by_id ────────────────────────────────────────────────

    def test_get_by_id_returns_payment_via_when_found(
        self, payment_via_repo: InMemoryPaymentViaRepository
    ) -> None:
        pv = _seed_payment_via(payment_via_repo)

        result = payment_via_repo.get_by_id(pv.payment_via_id)

        assert result is not None
        assert result.payment_via_id == pv.payment_via_id
        assert result.name == pv.name

    def test_get_by_id_returns_none_when_not_found(
        self, payment_via_repo: InMemoryPaymentViaRepository
    ) -> None:
        result = payment_via_repo.get_by_id(uuid4())
        assert result is None

    # ── BaseRepo: add ──────────────────────────────────────────────────────

    def test_add_stores_payment_via(
        self, payment_via_repo: InMemoryPaymentViaRepository
    ) -> None:
        pv = PaymentVia(name="Transferencia", payment_via_id=uuid4())

        result = payment_via_repo.add(pv)

        assert result == pv
        assert payment_via_repo.get_by_id(pv.payment_via_id) == pv

    # ── BaseRepo: get_all ──────────────────────────────────────────────────

    def test_get_all_returns_all_payment_vias(
        self, payment_via_repo: InMemoryPaymentViaRepository
    ) -> None:
        p1 = _seed_payment_via(payment_via_repo, name="Via One")
        p2 = _seed_payment_via(payment_via_repo, name="Via Two")

        result = payment_via_repo.get_all()

        assert len(result) == 2
        assert p1 in result
        assert p2 in result

    def test_get_all_returns_empty_when_no_payment_vias(
        self, payment_via_repo: InMemoryPaymentViaRepository
    ) -> None:
        result = payment_via_repo.get_all()
        assert result == []

    # ── BaseRepo: exists ───────────────────────────────────────────────────

    def test_exists_returns_true_when_match(
        self, payment_via_repo: InMemoryPaymentViaRepository
    ) -> None:
        _seed_payment_via(payment_via_repo, name="Unique Via")

        assert payment_via_repo.exists({"name": "Unique Via"}) is True

    def test_exists_returns_false_when_no_match(
        self, payment_via_repo: InMemoryPaymentViaRepository
    ) -> None:
        _seed_payment_via(payment_via_repo, name="Unique Via")

        assert payment_via_repo.exists({"name": "Other Via"}) is False

    # ── BaseRepo: update ───────────────────────────────────────────────────

    def test_update_returns_true_and_modifies(
        self, payment_via_repo: InMemoryPaymentViaRepository
    ) -> None:
        pv = _seed_payment_via(payment_via_repo, name="Original")
        updated = PaymentVia(payment_via_id=pv.payment_via_id, name="Modified")

        result = payment_via_repo.update(pv.payment_via_id, updated)

        assert result is True
        stored = payment_via_repo.get_by_id(pv.payment_via_id)
        assert stored is not None
        assert stored.name == "Modified"

    def test_update_returns_false_when_not_found(
        self, payment_via_repo: InMemoryPaymentViaRepository
    ) -> None:
        p = PaymentVia(name="Ghost")
        result = payment_via_repo.update(p.payment_via_id, p)
        assert result is False

    # ── BaseRepo: delete ───────────────────────────────────────────────────

    def test_delete_removes_payment_via(
        self, payment_via_repo: InMemoryPaymentViaRepository
    ) -> None:
        pv = _seed_payment_via(payment_via_repo)

        payment_via_repo.delete(pv.payment_via_id)

        assert payment_via_repo.get_by_id(pv.payment_via_id) is None

    def test_delete_nonexistent_does_nothing(
        self, payment_via_repo: InMemoryPaymentViaRepository
    ) -> None:
        payment_via_repo.delete(uuid4())

    # ── BaseRepo: get_by_ids ───────────────────────────────────────────────

    def test_get_by_ids_returns_matching(
        self, payment_via_repo: InMemoryPaymentViaRepository
    ) -> None:
        p1 = _seed_payment_via(payment_via_repo)
        p2 = _seed_payment_via(payment_via_repo)
        p3 = _seed_payment_via(payment_via_repo)

        result = payment_via_repo.get_by_ids([p1.payment_via_id, p3.payment_via_id])

        assert len(result) == 2
        assert p1 in result
        assert p3 in result
        assert p2 not in result

    def test_get_by_ids_returns_empty_when_none_match(
        self, payment_via_repo: InMemoryPaymentViaRepository
    ) -> None:
        _seed_payment_via(payment_via_repo)
        result = payment_via_repo.get_by_ids([uuid4(), uuid4()])
        assert result == []

    # ── PaymentViaRepoPort: get_by_name ────────────────────────────────────

    def test_get_by_name_returns_payment_via_when_found(
        self, payment_via_repo: InMemoryPaymentViaRepository
    ) -> None:
        _seed_payment_via(payment_via_repo, name="Transferencia")

        result = payment_via_repo.get_by_name("Transferencia")

        assert result is not None
        assert result.name == "Transferencia"

    def test_get_by_name_returns_none_when_not_found(
        self, payment_via_repo: InMemoryPaymentViaRepository
    ) -> None:
        result = payment_via_repo.get_by_name("NonExistent")
        assert result is None

    # ── PaymentViaRepoPort: named getters ──────────────────────────────────

    def test_get_transferencia_returns_transferencia(
        self, payment_via_repo: InMemoryPaymentViaRepository
    ) -> None:
        _seed_payment_via(payment_via_repo, name="Transferencia")

        result = payment_via_repo.get_transferencia()

        assert result is not None
        assert result.name == "Transferencia"

    def test_get_nc_returns_nota_de_credito(
        self, payment_via_repo: InMemoryPaymentViaRepository
    ) -> None:
        _seed_payment_via(payment_via_repo, name="Nota de Crédito")

        result = payment_via_repo.get_nc()

        assert result is not None
        assert result.name == "Nota de Crédito"

    def test_named_getter_returns_none_when_not_found(
        self, payment_via_repo: InMemoryPaymentViaRepository
    ) -> None:
        assert payment_via_repo.get_transferencia() is None
        assert payment_via_repo.get_nc() is None

    # ── _Activatable ───────────────────────────────────────────────────────

    def test_activate_sets_active_true(
        self, payment_via_repo: InMemoryPaymentViaRepository
    ) -> None:
        pv = _seed_payment_via(payment_via_repo, active=False)

        result = payment_via_repo.activate(pv.payment_via_id)

        assert result is True
        assert payment_via_repo.get_by_id(pv.payment_via_id).active is True

    def test_inactivate_sets_active_false(
        self, payment_via_repo: InMemoryPaymentViaRepository
    ) -> None:
        pv = _seed_payment_via(payment_via_repo, active=True)

        result = payment_via_repo.inactivate(pv.payment_via_id)

        assert result is True
        assert payment_via_repo.get_by_id(pv.payment_via_id).active is False

    def test_activate_returns_false_when_not_found(
        self, payment_via_repo: InMemoryPaymentViaRepository
    ) -> None:
        assert payment_via_repo.activate(uuid4()) is False

    def test_inactivate_returns_false_when_not_found(
        self, payment_via_repo: InMemoryPaymentViaRepository
    ) -> None:
        assert payment_via_repo.inactivate(uuid4()) is False


# ═══════════════════════════════════════════════════════════════════════════════
# ClaimKind Tests
# ═══════════════════════════════════════════════════════════════════════════════


class TestClaimKindRepo:
    """Tests for InMemoryClaimKindRepository — BaseRepo + ClaimKindRepoPort + _Activatable."""

    # ── BaseRepo: get_by_id ────────────────────────────────────────────────

    def test_get_by_id_returns_claim_kind_when_found(
        self, claim_kind_repo: InMemoryClaimKindRepository
    ) -> None:
        ck = _seed_claim_kind(claim_kind_repo)

        result = claim_kind_repo.get_by_id(ck.claim_kind_id)

        assert result is not None
        assert result.claim_kind_id == ck.claim_kind_id
        assert result.name == ck.name

    def test_get_by_id_returns_none_when_not_found(
        self, claim_kind_repo: InMemoryClaimKindRepository
    ) -> None:
        result = claim_kind_repo.get_by_id(uuid4())
        assert result is None

    # ── BaseRepo: add ──────────────────────────────────────────────────────

    def test_add_stores_claim_kind(
        self, claim_kind_repo: InMemoryClaimKindRepository
    ) -> None:
        ck = ClaimKind(name="SOS", claim_kind_id=uuid4())

        result = claim_kind_repo.add(ck)

        assert result == ck
        assert claim_kind_repo.get_by_id(ck.claim_kind_id) == ck

    # ── BaseRepo: get_all ──────────────────────────────────────────────────

    def test_get_all_returns_all_claim_kinds(
        self, claim_kind_repo: InMemoryClaimKindRepository
    ) -> None:
        c1 = _seed_claim_kind(claim_kind_repo, name="Kind One")
        c2 = _seed_claim_kind(claim_kind_repo, name="Kind Two")

        result = claim_kind_repo.get_all()

        assert len(result) == 2
        assert c1 in result
        assert c2 in result

    def test_get_all_returns_empty_when_no_claim_kinds(
        self, claim_kind_repo: InMemoryClaimKindRepository
    ) -> None:
        result = claim_kind_repo.get_all()
        assert result == []

    # ── BaseRepo: exists ───────────────────────────────────────────────────

    def test_exists_returns_true_when_match(
        self, claim_kind_repo: InMemoryClaimKindRepository
    ) -> None:
        _seed_claim_kind(claim_kind_repo, name="Unique Kind")

        assert claim_kind_repo.exists({"name": "Unique Kind"}) is True

    def test_exists_returns_false_when_no_match(
        self, claim_kind_repo: InMemoryClaimKindRepository
    ) -> None:
        _seed_claim_kind(claim_kind_repo, name="Unique Kind")

        assert claim_kind_repo.exists({"name": "Other Kind"}) is False

    # ── BaseRepo: update ───────────────────────────────────────────────────

    def test_update_returns_true_and_modifies(
        self, claim_kind_repo: InMemoryClaimKindRepository
    ) -> None:
        ck = _seed_claim_kind(claim_kind_repo, name="Original")
        updated = ClaimKind(claim_kind_id=ck.claim_kind_id, name="Modified")

        result = claim_kind_repo.update(ck.claim_kind_id, updated)

        assert result is True
        stored = claim_kind_repo.get_by_id(ck.claim_kind_id)
        assert stored is not None
        assert stored.name == "Modified"

    def test_update_returns_false_when_not_found(
        self, claim_kind_repo: InMemoryClaimKindRepository
    ) -> None:
        c = ClaimKind(name="Ghost")
        result = claim_kind_repo.update(c.claim_kind_id, c)
        assert result is False

    # ── BaseRepo: delete ───────────────────────────────────────────────────

    def test_delete_removes_claim_kind(
        self, claim_kind_repo: InMemoryClaimKindRepository
    ) -> None:
        ck = _seed_claim_kind(claim_kind_repo)

        claim_kind_repo.delete(ck.claim_kind_id)

        assert claim_kind_repo.get_by_id(ck.claim_kind_id) is None

    def test_delete_nonexistent_does_nothing(
        self, claim_kind_repo: InMemoryClaimKindRepository
    ) -> None:
        claim_kind_repo.delete(uuid4())

    # ── BaseRepo: get_by_ids ───────────────────────────────────────────────

    def test_get_by_ids_returns_matching(
        self, claim_kind_repo: InMemoryClaimKindRepository
    ) -> None:
        c1 = _seed_claim_kind(claim_kind_repo)
        c2 = _seed_claim_kind(claim_kind_repo)
        c3 = _seed_claim_kind(claim_kind_repo)

        result = claim_kind_repo.get_by_ids([c1.claim_kind_id, c3.claim_kind_id])

        assert len(result) == 2
        assert c1 in result
        assert c3 in result
        assert c2 not in result

    def test_get_by_ids_returns_empty_when_none_match(
        self, claim_kind_repo: InMemoryClaimKindRepository
    ) -> None:
        _seed_claim_kind(claim_kind_repo)
        result = claim_kind_repo.get_by_ids([uuid4(), uuid4()])
        assert result == []

    # ── ClaimKindRepoPort: get_by_name ─────────────────────────────────────

    def test_get_by_name_returns_claim_kind_when_found(
        self, claim_kind_repo: InMemoryClaimKindRepository
    ) -> None:
        _seed_claim_kind(claim_kind_repo, name="SOS")

        result = claim_kind_repo.get_by_name("SOS")

        assert result is not None
        assert result.name == "SOS"

    def test_get_by_name_returns_none_when_not_found(
        self, claim_kind_repo: InMemoryClaimKindRepository
    ) -> None:
        result = claim_kind_repo.get_by_name("NonExistent")
        assert result is None

    # ── _Activatable ───────────────────────────────────────────────────────

    def test_activate_sets_active_true(
        self, claim_kind_repo: InMemoryClaimKindRepository
    ) -> None:
        ck = _seed_claim_kind(claim_kind_repo, active=False)

        result = claim_kind_repo.activate(ck.claim_kind_id)

        assert result is True
        assert claim_kind_repo.get_by_id(ck.claim_kind_id).active is True

    def test_inactivate_sets_active_false(
        self, claim_kind_repo: InMemoryClaimKindRepository
    ) -> None:
        ck = _seed_claim_kind(claim_kind_repo, active=True)

        result = claim_kind_repo.inactivate(ck.claim_kind_id)

        assert result is True
        assert claim_kind_repo.get_by_id(ck.claim_kind_id).active is False

    def test_activate_returns_false_when_not_found(
        self, claim_kind_repo: InMemoryClaimKindRepository
    ) -> None:
        assert claim_kind_repo.activate(uuid4()) is False

    def test_inactivate_returns_false_when_not_found(
        self, claim_kind_repo: InMemoryClaimKindRepository
    ) -> None:
        assert claim_kind_repo.inactivate(uuid4()) is False
