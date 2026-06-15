from contextlib import contextmanager
from typing import Any
from uuid import UUID

import sqlalchemy as sa

from src.domain.models.entities import GroupClaim
from src.infrastructure.database.connection import get_connection
from src.infrastructure.database.tables import claims, group_claims


class SqlAlchemyGroupClaimRepository:
    """Implementación de GroupClaimRepoPort usando SQLAlchemy Core."""

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
    def _row_to_entity(row: sa.Row) -> GroupClaim:
        return GroupClaim(
            group_id=row.group_id,
            name=row.name,
            external_reference=row.external_reference,
            description=row.description,
            created_at=row.created_at,
        )

    # ── BaseRepo ──────────────────────────────────────────────────────────────

    def add(self, model: GroupClaim) -> GroupClaim:
        with self._get_conn() as conn:
            conn.execute(
                sa.insert(group_claims).values(
                    group_id=model.group_id,
                    name=model.name,
                    external_reference=model.external_reference,
                    description=model.description,
                    created_at=model.created_at,
                )
            )
        return model

    def get_by_id(self, id: UUID) -> GroupClaim | None:
        with self._get_conn() as conn:
            row = conn.execute(
                sa.select(group_claims).where(group_claims.c.group_id == id)
            ).fetchone()
        return self._row_to_entity(row) if row else None

    def delete(self, id: UUID) -> None:
        with self._get_conn() as conn:
            conn.execute(sa.delete(group_claims).where(group_claims.c.group_id == id))

    def update(self, id: UUID, model: GroupClaim) -> bool:
        with self._get_conn() as conn:
            result = conn.execute(
                sa.update(group_claims)
                .where(group_claims.c.group_id == id)
                .values(
                    name=model.name,
                    external_reference=model.external_reference,
                    description=model.description,
                )
            )
        return result.rowcount > 0

    def get_all(self) -> list[GroupClaim]:
        with self._get_conn() as conn:
            rows = conn.execute(
                sa.select(group_claims).order_by(group_claims.c.name)
            ).fetchall()
        return [self._row_to_entity(r) for r in rows]

    def exists(self, data: dict[str, Any]) -> bool:
        conditions = [group_claims.c[k] == v for k, v in data.items()]
        with self._get_conn() as conn:
            row = conn.execute(
                sa.select(group_claims.c.group_id).where(sa.and_(*conditions))
            ).fetchone()
        return row is not None

    def get_by_ids(self, ids: list[UUID]) -> list[GroupClaim]:
        with self._get_conn() as conn:
            rows = conn.execute(
                sa.select(group_claims).where(group_claims.c.group_id.in_(ids))
            ).fetchall()
        return [self._row_to_entity(r) for r in rows]

    # ── GroupClaimRepoPort ───────────────────────────────────────────────────

    def get_by_group_name(self, group_name: str) -> GroupClaim | None:
        with self._get_conn() as conn:
            row = conn.execute(
                sa.select(group_claims).where(group_claims.c.name == group_name)
            ).fetchone()
        return self._row_to_entity(row) if row else None

    def get_by_text_like(self, text: str) -> list[GroupClaim]:
        with self._get_conn() as conn:
            rows = conn.execute(
                sa.select(group_claims).where(group_claims.c.name.ilike(f"%{text}%"))
            ).fetchall()
        return [self._row_to_entity(r) for r in rows]

    def get_by_claim_id(self, claim_id: UUID) -> GroupClaim | None:
        with self._get_conn() as conn:
            row = conn.execute(
                sa.select(group_claims)
                .select_from(
                    group_claims.join(
                        claims, claims.c.group_id == group_claims.c.group_id
                    )
                )
                .where(claims.c.claim_id == claim_id)
            ).fetchone()
        return self._row_to_entity(row) if row else None

    # ── _DocReachable stubs ──────────────────────────────────────────────────

    def get_by_document_id(self, document_id: UUID) -> list[GroupClaim]:
        return []

    def get_by_document(self, document: bytes) -> list[GroupClaim]:
        return []
