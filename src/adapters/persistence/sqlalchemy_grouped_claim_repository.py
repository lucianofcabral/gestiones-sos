from contextlib import contextmanager
from typing import Any
from uuid import UUID

import sqlalchemy as sa

from src.domain.models.entities import GroupedClaim
from src.infrastructure.database.connection import get_connection
from src.infrastructure.database.tables import grouped_claims


class SqlAlchemyGroupedClaimRepository:
    """Implementación de GroupedClaimRepoPort usando SQLAlchemy Core.

    Es agnóstico al motor de base de datos (PostgreSQL, MySQL, SQLite, etc.).
    Si se construye con ``conn``, opera dentro de una transacción externa (UoW).
    Sin ``conn`` abre y cierra su propia conexión en cada método.
    """

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
    def _row_to_grouped_claim(row: sa.Row) -> GroupedClaim:
        return GroupedClaim(
            grouped_claim_id=row.grouped_claim_id,
            claim_id=row.claim_id,
            group_claim_id=row.group_claim_id,
            notes=row.notes,
            created_at=row.created_at,
        )

    # ── BaseRepo ──────────────────────────────────────────────────────────────

    def add(self, model: GroupedClaim) -> GroupedClaim:
        with self._get_conn() as conn:
            conn.execute(
                sa.insert(grouped_claims).values(
                    grouped_claim_id=model.grouped_claim_id,
                    claim_id=model.claim_id,
                    group_claim_id=model.group_claim_id,
                    notes=model.notes,
                    created_at=model.created_at,
                )
            )
        return model

    def get_by_id(self, id: UUID) -> GroupedClaim | None:
        with self._get_conn() as conn:
            row = conn.execute(
                sa.select(grouped_claims).where(
                    grouped_claims.c.grouped_claim_id == id
                )
            ).fetchone()
        return self._row_to_grouped_claim(row) if row else None

    def delete(self, id: UUID) -> None:
        with self._get_conn() as conn:
            conn.execute(
                sa.delete(grouped_claims).where(
                    grouped_claims.c.grouped_claim_id == id
                )
            )

    def update(self, id: UUID, model: GroupedClaim) -> bool:
        with self._get_conn() as conn:
            result = conn.execute(
                sa.update(grouped_claims)
                .where(grouped_claims.c.grouped_claim_id == id)
                .values(
                    claim_id=model.claim_id,
                    group_claim_id=model.group_claim_id,
                    notes=model.notes,
                )
            )
        return result.rowcount > 0

    def get_all(self) -> list[GroupedClaim]:
        with self._get_conn() as conn:
            rows = conn.execute(
                sa.select(grouped_claims).order_by(
                    grouped_claims.c.created_at.desc()
                )
            ).fetchall()
        return [self._row_to_grouped_claim(r) for r in rows]

    def exists(self, data: dict[str, Any]) -> bool:
        conditions = [grouped_claims.c[k] == v for k, v in data.items()]
        with self._get_conn() as conn:
            row = conn.execute(
                sa.select(grouped_claims.c.grouped_claim_id).where(
                    sa.and_(*conditions)
                )
            ).fetchone()
        return row is not None

    def get_by_ids(self, ids: list[UUID]) -> list[GroupedClaim]:
        with self._get_conn() as conn:
            rows = conn.execute(
                sa.select(grouped_claims).where(
                    grouped_claims.c.grouped_claim_id.in_(ids)
                )
            ).fetchall()
        return [self._row_to_grouped_claim(r) for r in rows]

    # ── GroupedClaimRepoPort extra ────────────────────────────────────────────

    def get_by_claim_id(self, claim_id: UUID) -> GroupedClaim | None:
        with self._get_conn() as conn:
            row = conn.execute(
                sa.select(grouped_claims).where(
                    grouped_claims.c.claim_id == claim_id
                )
            ).fetchone()
        return self._row_to_grouped_claim(row) if row else None
