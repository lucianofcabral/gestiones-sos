"""Tests for the audit wrapper — AuditRepositoryWrapper + audit_context."""

from uuid import UUID, uuid4

import pytest
from pydantic import BaseModel

from src.application.services.audit_context import get_audit_user, set_audit_user
from src.application.services.audit_wrapper import AuditRepositoryWrapper
from src.adapters.persistence.inmemory_audit_repository import (
    InMemoryAuditRepository,
)
from src.domain.models.audit_log import AuditLog


# ── Fixtures ──────────────────────────────────────────────────────────────────


class DummyEntity(BaseModel):
    dummy_id: UUID
    name: str
    active: bool = True


class _DummyRepo:
    """In-memory repo that mimics BaseRepo for test purposes."""

    def __init__(self):
        self._store: dict[UUID, DummyEntity] = {}

    def add(self, model: DummyEntity) -> DummyEntity:
        self._store[model.dummy_id] = model
        return model

    def get_by_id(self, id: UUID) -> DummyEntity | None:
        return self._store.get(id)

    def get_all(self) -> list[DummyEntity]:
        return list(self._store.values())

    def exists(self, data: dict) -> bool:
        return any(
            all(getattr(e, k) == v for k, v in data.items())
            for e in self._store.values()
        )

    def get_by_ids(self, ids: list[UUID]) -> list[DummyEntity]:
        return [e for i, e in self._store.items() if i in ids]

    def update(self, id: UUID, model: DummyEntity) -> bool:
        if id in self._store:
            self._store[id] = model
            return True
        return False

    def delete(self, id: UUID) -> None:
        self._store.pop(id, None)

    def inactivate(self, id: UUID) -> bool:
        if id in self._store:
            self._store[id].active = False
            return True
        return False

    def activate(self, id: UUID) -> bool:
        if id in self._store:
            self._store[id].active = True
            return True
        return False

    # extra method to test __getattr__ delegation
    def get_by_name(self, name: str) -> DummyEntity | None:
        for e in self._store.values():
            if e.name == name:
                return e
        return None


@pytest.fixture
def audit_repo():
    return InMemoryAuditRepository()


@pytest.fixture
def inner():
    return _DummyRepo()


@pytest.fixture
def wrapper(inner, audit_repo):
    return AuditRepositoryWrapper(
        inner=inner, audit_repo=audit_repo, entity_type="dummy"
    )


@pytest.fixture
def entity():
    return DummyEntity(dummy_id=uuid4(), name="original")


# ── audit_context tests ───────────────────────────────────────────────────────


class TestAuditContext:
    def test_default_is_none(self):
        assert get_audit_user() is None

    def test_set_and_get(self):
        uid = uuid4()
        set_audit_user(uid)
        assert get_audit_user() == uid

    def test_set_none(self):
        uid = uuid4()
        set_audit_user(uid)
        assert get_audit_user() == uid
        set_audit_user(None)
        assert get_audit_user() is None

    def test_context_isolation(self):
        """ContextVar isolation — not a true concurrency test but checks assignment."""
        uid1, uid2 = uuid4(), uuid4()
        set_audit_user(uid1)
        assert get_audit_user() == uid1
        set_audit_user(uid2)
        assert get_audit_user() == uid2


# ── AuditRepositoryWrapper tests ──────────────────────────────────────────────


class TestAuditWrapperUpdate:
    def test_logs_update_with_old_and_new_values(self, wrapper, inner, audit_repo, entity):
        inner.add(entity)
        updated = entity.model_copy(update={"name": "modified"})
        wrapper.update(entity.dummy_id, updated)

        logs = audit_repo.get_all()
        assert len(logs) == 1
        log = logs[0]
        assert log.action == "update"
        assert log.entity_type == "dummy"
        assert log.entity_id == entity.dummy_id
        assert log.old_values["name"] == "original"
        assert log.new_values["name"] == "modified"

    def test_does_not_log_when_id_not_found(self, wrapper, audit_repo, entity):
        result = wrapper.update(uuid4(), entity)
        assert not result
        assert len(audit_repo.get_all()) == 0

    def test_uses_audit_user_when_set(self, wrapper, inner, audit_repo, entity):
        uid = uuid4()
        set_audit_user(uid)
        inner.add(entity)
        wrapper.update(entity.dummy_id, entity.model_copy(update={"name": "x"}))
        set_audit_user(None)  # cleanup

        log = audit_repo.get_all()[0]
        assert log.performed_by == uid

    def test_performed_by_is_none_when_no_user_set(self, wrapper, inner, audit_repo, entity):
        set_audit_user(None)
        inner.add(entity)
        wrapper.update(entity.dummy_id, entity.model_copy(update={"name": "x"}))
        log = audit_repo.get_all()[0]
        assert log.performed_by is None


class TestAuditWrapperDelete:
    def test_logs_delete_with_old_values(self, wrapper, inner, audit_repo, entity):
        inner.add(entity)
        wrapper.delete(entity.dummy_id)

        logs = audit_repo.get_all()
        assert len(logs) == 1
        log = logs[0]
        assert log.action == "delete"
        assert log.entity_id == entity.dummy_id
        assert log.old_values["name"] == "original"

    def test_no_log_when_id_not_found(self, wrapper, audit_repo):
        wrapper.delete(uuid4())
        assert len(audit_repo.get_all()) == 0


class TestAuditWrapperInactivate:
    def test_logs_inactivate(self, wrapper, inner, audit_repo, entity):
        inner.add(entity)
        result = wrapper.inactivate(entity.dummy_id)
        assert result

        logs = audit_repo.get_all()
        assert len(logs) == 1
        assert logs[0].action == "inactivate"
        assert logs[0].entity_id == entity.dummy_id
        assert logs[0].old_values["name"] == "original"

    def test_no_log_when_id_not_found(self, wrapper, audit_repo):
        result = wrapper.inactivate(uuid4())
        assert not result
        assert len(audit_repo.get_all()) == 0


class TestAuditWrapperActivate:
    def test_logs_activate(self, wrapper, inner, audit_repo, entity):
        inner.add(entity)
        wrapper.inactivate(entity.dummy_id)
        result = wrapper.activate(entity.dummy_id)
        assert result

        logs = audit_repo.get_all()
        # inactivate + activate
        assert len(logs) == 2
        assert logs[0].action == "activate"
        assert logs[1].action == "inactivate"


class TestAuditWrapperAdd:
    def test_logs_create_with_new_values(self, wrapper, audit_repo, entity):
        wrapper.add(entity)

        logs = audit_repo.get_all()
        assert len(logs) == 1
        log = logs[0]
        assert log.action == "create"
        assert log.entity_id == entity.dummy_id
        assert log.new_values["name"] == "original"
        assert log.old_values is None


class TestAuditWrapperPassthrough:
    def test_get_by_id_delegates(self, wrapper, inner, entity):
        inner.add(entity)
        assert wrapper.get_by_id(entity.dummy_id) == entity

    def test_get_all_delegates(self, wrapper, inner, entity):
        inner.add(entity)
        assert wrapper.get_all() == [entity]

    def test_exists_delegates(self, wrapper, inner, entity):
        inner.add(entity)
        assert wrapper.exists({"name": "original"})
        assert not wrapper.exists({"name": "nope"})

    def test_get_by_ids_delegates(self, wrapper, inner, entity):
        inner.add(entity)
        assert wrapper.get_by_ids([entity.dummy_id]) == [entity]

    def test_get_by_name_delegated_via_getattr(self, wrapper, inner, entity):
        """Extra method on inner not in the wrapper should work via __getattr__."""
        inner.add(entity)
        result = wrapper.get_by_name("original")
        assert result == entity
        assert wrapper.get_by_name("nope") is None


class TestAuditWrapperMultipleOps:
    def test_three_ops_produce_three_logs(self, wrapper, inner, audit_repo, entity):
        wrapper.add(entity)
        wrapper.update(entity.dummy_id, entity.model_copy(update={"name": "v2"}))
        wrapper.delete(entity.dummy_id)

        logs = audit_repo.get_all()
        assert len(logs) == 3
        assert [l.action for l in logs] == ["delete", "update", "create"]
