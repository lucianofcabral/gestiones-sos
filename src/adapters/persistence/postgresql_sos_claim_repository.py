from typing import Any
from uuid import UUID

import sqlalchemy as sa

from src.domain.models.entities import SosClaim
from src.infrastructure.database.connection import get_connection
from src.infrastructure.database.tables import sos_claims


class PostgreSQLSosClaimRepository:
    """Implementación de SosClaimRepoPort usando SQLAlchemy Core + PostgreSQL."""

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
        with get_connection() as conn:
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
            conn.commit()
        return model

    def get_by_id(self, id: UUID) -> SosClaim | None:
        with get_connection() as conn:
            row = conn.execute(
                sa.select(sos_claims).where(sos_claims.c.sos_claim_id == id)
            ).fetchone()
        return self._row_to_sos_claim(row) if row else None

    def delete(self, id: UUID) -> None:
        with get_connection() as conn:
            conn.execute(sa.delete(sos_claims).where(sos_claims.c.sos_claim_id == id))
            conn.commit()

    def update(self, id: UUID, model: SosClaim) -> bool:
        with get_connection() as conn:
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
            conn.commit()
        return result.rowcount > 0

    def get_all(self) -> list[SosClaim]:
        with get_connection() as conn:
            rows = conn.execute(sa.select(sos_claims)).fetchall()
        return [self._row_to_sos_claim(r) for r in rows]

    def exists(self, data: dict[str, Any]) -> bool:
        conditions = [sos_claims.c[k] == v for k, v in data.items()]
        with get_connection() as conn:
            row = conn.execute(
                sa.select(sos_claims.c.sos_claim_id).where(sa.and_(*conditions))
            ).fetchone()
        return row is not None

    def get_by_ids(self, ids: list[UUID]) -> list[SosClaim]:
        with get_connection() as conn:
            rows = conn.execute(
                sa.select(sos_claims).where(sos_claims.c.sos_claim_id.in_(ids))
            ).fetchall()
        return [self._row_to_sos_claim(r) for r in rows]

    # ── _Activatable ──────────────────────────────────────────────────────────

    def activate(self, id: UUID) -> bool:
        with get_connection() as conn:
            result = conn.execute(
                sa.update(sos_claims).where(sos_claims.c.sos_claim_id == id).values(active=True)
            )
            conn.commit()
        return result.rowcount > 0

    def inactivate(self, id: UUID) -> bool:
        with get_connection() as conn:
            result = conn.execute(
                sa.update(sos_claims).where(sos_claims.c.sos_claim_id == id).values(active=False)
            )
            conn.commit()
        return result.rowcount > 0

    # ── SosClaimRepoPort extra ────────────────────────────────────────────────

    def get_claims_by_claim_id(self, claim_id: UUID) -> list[SosClaim]:
        with get_connection() as conn:
            rows = conn.execute(
                sa.select(sos_claims).where(sos_claims.c.claim_id == claim_id)
            ).fetchall()
        return [self._row_to_sos_claim(r) for r in rows]

    def get_by_number(self, claim_number: int) -> SosClaim | None:
        with get_connection() as conn:
            row = conn.execute(
                sa.select(sos_claims).where(sos_claims.c.gestion == claim_number)
            ).fetchone()
        return self._row_to_sos_claim(row) if row else None

    def get_by_status(self, status: str) -> list[SosClaim]:
        with get_connection() as conn:
            rows = conn.execute(
                sa.select(sos_claims).where(sos_claims.c.status == status)
            ).fetchall()
        return [self._row_to_sos_claim(r) for r in rows]

    def get_by_text_like(self, text: str) -> SosClaim | None:
        pattern = f"%{text}%"
        with get_connection() as conn:
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
