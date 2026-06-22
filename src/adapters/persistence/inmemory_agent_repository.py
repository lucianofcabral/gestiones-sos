from typing import Any
from uuid import UUID

from src.domain.models.entities import Agent


class InMemoryAgentRepository:
    def __init__(self) -> None:
        self._store: list[Agent] = []

    # ── BaseRepo ──────────────────────────────────────────────────────────────

    def add(self, model: Agent) -> Agent:
        self._store.append(model)
        return model

    def get_by_id(self, id: UUID) -> Agent | None:
        return next((a for a in self._store if a.agent_id == id), None)

    def delete(self, id: UUID) -> None:
        self._store = [a for a in self._store if a.agent_id != id]

    def update(self, id: UUID, model: Agent) -> bool:
        for i, a in enumerate(self._store):
            if a.agent_id == id:
                self._store[i] = model
                return True
        return False

    def get_all(self) -> list[Agent]:
        return list(self._store)

    def exists(self, data: dict[str, Any]) -> bool:
        return any(
            all(getattr(a, k) == v for k, v in data.items()) for a in self._store
        )

    def get_by_ids(self, ids: list[UUID]) -> list[Agent]:
        return [a for a in self._store if a.agent_id in ids]

    # ── AgentRepoPort ─────────────────────────────────────────────────────────

    def get_by_name(self, name: str) -> Agent | None:
        return next((a for a in self._store if a.name == name), None)

    def get_sos(self) -> Agent | None:
        return self.get_by_name("SOS")

    def get_sm(self) -> Agent | None:
        return self.get_by_name("SM")

    def get_prestador(self) -> Agent | None:
        return self.get_by_name("Prestador")

    def get_asegurado(self) -> Agent | None:
        return self.get_by_name("Asegurado")

    # ── _Activatable ──────────────────────────────────────────────────────────

    def activate(self, id: UUID) -> bool:
        for a in self._store:
            if a.agent_id == id:
                a.active = True
                return True
        return False

    def inactivate(self, id: UUID) -> bool:
        for a in self._store:
            if a.agent_id == id:
                a.active = False
                return True
        return False
