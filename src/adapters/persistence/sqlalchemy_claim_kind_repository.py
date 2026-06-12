from contextlib import contextmanager
from typing import Any
from uuid import UUID

import sqlalchemy as sa

from src.domain.models.entities import ClaimKind
from src.infrastructure.database.connection import get_connection
from src.infrastructure.database.tables import claim_kinds


class SqlAlchemyClaimKindRepository:
    """Implementación de ClaimKindRepoPort usando SQLAlchemy Core."""

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
    def _row_to_entity(row: sa.Row) -> ClaimKind:
        return ClaimKind(
            claim_kind_id=row.claim_kind_id,
            name=row.name,
            active=row.active,
            created_at=row.created_at,
        )

    # ── BaseRepo ──────────────────────────────────────────────────────────────

    def add(self, model: ClaimKind) -> ClaimKind:
        with self._get_conn() as conn:
            conn.execute(
                sa.insert(claim_kinds).values(
                    claim_kind_id=model.claim_kind_id,
                    name=model.name,
                    active=model.active,
                    created_at=model.created_at,
                )
            )
        return model

    def get_by_id(self, id: UUID) -> ClaimKind | None:
        with self._get_conn() as conn:
            row = conn.execute(
                sa.select(claim_kinds).where(claim_kinds.c.claim_kind_id == id)
            ).fetchone()
        return self._row_to_entity(row) if row else None

    def delete(self, id: UUID) -> None:
        with self._get_conn() as conn:
            conn.execute(sa.delete(claim_kinds).where(claim_kinds.c.claim_kind_id == id))

    def update(self, id: UUID, model: ClaimKind) -> bool:
        with self._get_conn() as conn:
            result = conn.execute(
                sa.update(claim_kinds)
                .where(claim_kinds.c.claim_kind_id == id)
                .values(
                    name=model.name,
                    active=model.active,
                )
            )
        return result.rowcount > 0

    def get_all(self) -> list[ClaimKind]:
        with self._get_conn() as conn:
            rows = conn.execute(sa.select(claim_kinds)).fetchall()
        return [self._row_to_entity(r) for r in rows]

    def exists(self, data: dict[str, Any]) -> bool:
        conditions = [claim_kinds.c[k] == v for k, v in data.items()]
        with self._get_conn() as conn:
            row = conn.execute(
                sa.select(claim_kinds.c.claim_kind_id).where(sa.and_(*conditions))
            ).fetchone()
        return row is not None

    def get_by_ids(self, ids: list[UUID]) -> list[ClaimKind]:
        with self._get_conn() as conn:
            rows = conn.execute(
                sa.select(claim_kinds).where(claim_kinds.c.claim_kind_id.in_(ids))
            ).fetchall()
        return [self._row_to_entity(r) for r in rows]

    # ── ClaimKindRepoPort ─────────────────────────────────────────────────────

    def get_by_name(self, name: str) -> ClaimKind | None:
        with self._get_conn() as conn:
            row = conn.execute(
                sa.select(claim_kinds).where(claim_kinds.c.name == name)
            ).fetchone()
        return self._row_to_entity(row) if row else None

    # ── _Activatable ──────────────────────────────────────────────────────────

    def activate(self, id: UUID) -> bool:
        return self.update(id, ClaimKind(claim_kind_id=id, active=True))

    def inactivate(self, id: UUID) -> bool:
        return self.update(id, ClaimKind(claim_kind_id=id, active=False))
