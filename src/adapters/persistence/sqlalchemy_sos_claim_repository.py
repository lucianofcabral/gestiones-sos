from contextlib import contextmanager
from typing import Any
from uuid import UUID

import sqlalchemy as sa

from src.domain.models.entities import SosClaim
from src.infrastructure.database.connection import get_connection
from src.infrastructure.database.tables import sos_claims


class SqlAlchemySosClaimRepository:
    """Implementación de SosClaimRepoPort usando SQLAlchemy Core.

    Es agnóstico al motor de base de datos (PostgreSQL, MySQL, SQLite, etc.).
    Si se construye con ``conn``, opera dentro de una transacción externa (UoW).
    Sin ``conn`` abre y cierra su propia conexión en cada método.
    """

    def __init__(self, conn: "sa.Connection | None" = None) -> None:
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
    def _row_to_sos_claim(row: sa.Row) -> SosClaim:
        return SosClaim(
            sos_claim_id=row.sos_claim_id,
            claim_id=row.claim_id,
            gestion=row.gestion,
            category=row.category,
            reason=row.reason,
            load_user=row.load_user,
            response_user=row.response_user,
            status=row.status,
            itr=row.itr,
        )

    # ── BaseRepo ──────────────────────────────────────────────────────────────

    def add(self, model: SosClaim) -> SosClaim:
        with self._get_conn() as conn:
            conn.execute(
                sa.insert(sos_claims).values(
                    sos_claim_id=model.sos_claim_id,
                    claim_id=model.claim_id,
                    gestion=model.gestion,
                    category=model.category,
                    reason=model.reason,
                    load_user=model.load_user,
                    response_user=model.response_user,
                    status=model.status,
                    itr=model.itr,
                )
            )
        return model

    def get_by_id(self, id: UUID) -> SosClaim | None:
        with self._get_conn() as conn:
            row = conn.execute(
                sa.select(sos_claims).where(sos_claims.c.sos_claim_id == id)
            ).fetchone()
        return self._row_to_sos_claim(row) if row else None

    def delete(self, id: UUID) -> None:
        with self._get_conn() as conn:
            conn.execute(sa.delete(sos_claims).where(sos_claims.c.sos_claim_id == id))

    def update(self, id: UUID, model: SosClaim) -> bool:
        with self._get_conn() as conn:
            result = conn.execute(
                sa.update(sos_claims)
                .where(sos_claims.c.sos_claim_id == id)
                .values(
                    gestion=model.gestion,
                    category=model.category,
                    reason=model.reason,
                    load_user=model.load_user,
                    response_user=model.response_user,
                    status=model.status,
                    itr=model.itr,
                )
            )
        return result.rowcount > 0

    def get_all(self) -> list[SosClaim]:
        with self._get_conn() as conn:
            rows = conn.execute(sa.select(sos_claims)).fetchall()
        return [self._row_to_sos_claim(r) for r in rows]

    def exists(self, data: dict[str, Any]) -> bool:
        conditions = [sos_claims.c[k] == v for k, v in data.items()]
        with self._get_conn() as conn:
            row = conn.execute(
                sa.select(sos_claims.c.sos_claim_id).where(sa.and_(*conditions))
            ).fetchone()
        return row is not None

    def get_by_ids(self, ids: list[UUID]) -> list[SosClaim]:
        with self._get_conn() as conn:
            rows = conn.execute(
                sa.select(sos_claims).where(sos_claims.c.sos_claim_id.in_(ids))
            ).fetchall()
        return [self._row_to_sos_claim(r) for r in rows]

    # ── _Activatable ──────────────────────────────────────────────────────────

    def activate(self, id: UUID) -> bool:
        with self._get_conn() as conn:
            result = conn.execute(
                sa.update(sos_claims)
                .where(sos_claims.c.sos_claim_id == id)
                .values(active=True)
            )
        return result.rowcount > 0

    def inactivate(self, id: UUID) -> bool:
        with self._get_conn() as conn:
            result = conn.execute(
                sa.update(sos_claims)
                .where(sos_claims.c.sos_claim_id == id)
                .values(active=False)
            )
        return result.rowcount > 0

    # ── SosClaimRepoPort extra ────────────────────────────────────────────────

    def get_claims_by_claim_id(self, claim_id: UUID) -> list[SosClaim]:
        with self._get_conn() as conn:
            rows = conn.execute(
                sa.select(sos_claims).where(sos_claims.c.claim_id == claim_id)
            ).fetchall()
        return [self._row_to_sos_claim(r) for r in rows]

    def get_by_number(self, claim_number: int) -> SosClaim | None:
        with self._get_conn() as conn:
            row = conn.execute(
                sa.select(sos_claims).where(sos_claims.c.gestion == claim_number)
            ).fetchone()
        return self._row_to_sos_claim(row) if row else None

    def get_by_status(self, status: str) -> list[SosClaim]:
        with self._get_conn() as conn:
            rows = conn.execute(
                sa.select(sos_claims).where(sos_claims.c.status == status)
            ).fetchall()
        return [self._row_to_sos_claim(r) for r in rows]

    def get_by_text_like(self, text: str) -> SosClaim | None:
        pattern = f"%{text}%"
        with self._get_conn() as conn:
            row = conn.execute(
                sa.select(sos_claims).where(
                    sa.or_(
                        sos_claims.c.category.ilike(pattern),
                        sos_claims.c.reason.ilike(pattern),
                        sos_claims.c.load_user.ilike(pattern),
                    )
                )
            ).fetchone()
        return self._row_to_sos_claim(row) if row else None
