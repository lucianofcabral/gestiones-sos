from contextlib import contextmanager
from typing import Any
from uuid import UUID

import sqlalchemy as sa

from src.domain.models.entities import Agent
from src.infrastructure.database.connection import get_connection
from src.infrastructure.database.tables import agents


class SqlAlchemyAgentRepository:
    """Implementación de AgentRepoPort usando SQLAlchemy Core."""

    def __init__(self, conn: sa.Connection | None = None) -> None:
        self._conn = conn

    @contextmanager
    def _get_conn(self):
        if self._conn is not None:
            yield self._conn
        else:
            with get_connection() as c:
                yield c
                c.commit()

    # ── helper ────────────────────────────────────────────────────────────────

    @staticmethod
    def _row_to_entity(row: sa.Row) -> Agent:
        return Agent(
            agent_id=row.agent_id,
            name=row.name,
            active=row.active,
            created_at=row.created_at,
        )

    # ── BaseRepo ──────────────────────────────────────────────────────────────

    def add(self, model: Agent) -> Agent:
        with self._get_conn() as conn:
            conn.execute(
                sa.insert(agents).values(
                    agent_id=model.agent_id,
                    name=model.name,
                    active=model.active,
                    created_at=model.created_at,
                )
            )
        return model

    def get_by_id(self, id: UUID) -> Agent | None:
        with self._get_conn() as conn:
            row = conn.execute(
                sa.select(agents).where(agents.c.agent_id == id)
            ).fetchone()
        return self._row_to_entity(row) if row else None

    def delete(self, id: UUID) -> None:
        with self._get_conn() as conn:
            conn.execute(sa.delete(agents).where(agents.c.agent_id == id))

    def update(self, id: UUID, model: Agent) -> bool:
        with self._get_conn() as conn:
            result = conn.execute(
                sa.update(agents)
                .where(agents.c.agent_id == id)
                .values(
                    name=model.name,
                    active=model.active,
                )
            )
        return result.rowcount > 0

    def get_all(self) -> list[Agent]:
        with self._get_conn() as conn:
            rows = conn.execute(sa.select(agents)).fetchall()
        return [self._row_to_entity(r) for r in rows]

    def exists(self, data: dict[str, Any]) -> bool:
        conditions = [agents.c[k] == v for k, v in data.items()]
        with self._get_conn() as conn:
            row = conn.execute(
                sa.select(agents.c.agent_id).where(sa.and_(*conditions))
            ).fetchone()
        return row is not None

    def get_by_ids(self, ids: list[UUID]) -> list[Agent]:
        with self._get_conn() as conn:
            rows = conn.execute(
                sa.select(agents).where(agents.c.agent_id.in_(ids))
            ).fetchall()
        return [self._row_to_entity(r) for r in rows]

    # ── AgentRepoPort ─────────────────────────────────────────────────────────

    def get_by_name(self, name: str) -> Agent | None:
        with self._get_conn() as conn:
            row = conn.execute(
                sa.select(agents).where(agents.c.name == name)
            ).fetchone()
        return self._row_to_entity(row) if row else None

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
        return self.update(id, Agent(agent_id=id, active=True))

    def inactivate(self, id: UUID) -> bool:
        return self.update(id, Agent(agent_id=id, active=False))
