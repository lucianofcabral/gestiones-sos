from contextlib import contextmanager
from typing import Any
from uuid import UUID

import sqlalchemy as sa

from src.domain.models.entities import Claim
from src.infrastructure.database.connection import get_connection
from src.infrastructure.database.tables import claims


class SqlAlchemyClaimRepository:
    """Implementación de ClaimRepoPort usando SQLAlchemy Core.

    Es agnóstico al motor de base de datos (PostgreSQL, MySQL, SQLite, etc.).
    Si se construye con ``conn``, opera dentro de una transacción externa (UoW).
    Sin ``conn`` abre y cierra su propia conexión en cada método.
    """

    def __init__(self, conn: sa.Connection | None = None) -> None:
        self._conn = conn

    @contextmanager
    def _get_conn(self):
        if self._conn is not None:
            yield self._conn  # transacción externa: no hacer commit aquí
        else:
            with get_connection() as c:
                yield c
                c.commit()

    # ── helper ────────────────────────────────────────────────────────────────

    @staticmethod
    def _row_to_claim(row: sa.Row) -> Claim:
        return Claim(
            claim_id=row.claim_id,
            claim_kind_id=row.claim_kind_id,
            group_id=row.group_id,
            claimer_name=row.claimer_name,
            policy_number=row.policy_number,
            plate=row.plate,
            claimed_amount=float(row.claimed_amount),
            comment=row.comment,
            solved=row.solved,
            active=row.active,
            created_at=row.created_at,
        )

    # ── BaseRepo ──────────────────────────────────────────────────────────────

    def add(self, model: Claim) -> Claim:
        with self._get_conn() as conn:
            conn.execute(
                sa.insert(claims).values(
                    claim_id=model.claim_id,
                    claim_kind_id=model.claim_kind_id,
                    group_id=model.group_id,
                    claimer_name=model.claimer_name,
                    policy_number=model.policy_number,
                    plate=model.plate,
                    claimed_amount=model.claimed_amount,
                    comment=model.comment,
                    solved=model.solved,
                    active=model.active,
                    created_at=model.created_at,
                )
            )
        return model

    def get_by_id(self, id: UUID) -> Claim | None:
        with self._get_conn() as conn:
            row = conn.execute(
                sa.select(claims).where(claims.c.claim_id == id)
            ).fetchone()
        return self._row_to_claim(row) if row else None

    def delete(self, id: UUID) -> None:
        with self._get_conn() as conn:
            conn.execute(sa.delete(claims).where(claims.c.claim_id == id))

    def update(self, id: UUID, model: Claim) -> bool:
        with self._get_conn() as conn:
            result = conn.execute(
                sa.update(claims)
                .where(claims.c.claim_id == id)
                .values(
                    claimer_name=model.claimer_name,
                    policy_number=model.policy_number,
                    plate=model.plate,
                    claimed_amount=model.claimed_amount,
                    comment=model.comment,
                    solved=model.solved,
                    active=model.active,
                )
            )
        return result.rowcount > 0

    def get_all(self) -> list[Claim]:
        with self._get_conn() as conn:
            rows = conn.execute(sa.select(claims)).fetchall()
        return [self._row_to_claim(r) for r in rows]

    def exists(self, data: dict[str, Any]) -> bool:
        conditions = [claims.c[k] == v for k, v in data.items()]
        with self._get_conn() as conn:
            row = conn.execute(
                sa.select(claims.c.claim_id).where(sa.and_(*conditions))
            ).fetchone()
        return row is not None

    def get_by_ids(self, ids: list[UUID]) -> list[Claim]:
        with self._get_conn() as conn:
            rows = conn.execute(
                sa.select(claims).where(claims.c.claim_id.in_(ids))
            ).fetchall()
        return [self._row_to_claim(r) for r in rows]

    # ── _Activatable ──────────────────────────────────────────────────────────

    def activate(self, id: UUID) -> bool:
        with self._get_conn() as conn:
            result = conn.execute(
                sa.update(claims).where(claims.c.claim_id == id).values(active=True)
            )
        return result.rowcount > 0

    def inactivate(self, id: UUID) -> bool:
        with self._get_conn() as conn:
            result = conn.execute(
                sa.update(claims).where(claims.c.claim_id == id).values(active=False)
            )
        return result.rowcount > 0

    # ── _DocReachable ─────────────────────────────────────────────────────────

    def get_by_document_id(self, document_id: UUID) -> list[Claim]:
        # Requiere tabla document_entities — pendiente de implementar
        raise NotImplementedError("get_by_document_id requiere tabla document_entities")

    def get_by_document(self, document: bytes) -> list[Claim]:
        raise NotImplementedError("get_by_document requiere tabla document_entities")

    # ── ClaimRepoPort extra ───────────────────────────────────────────────────

    def get_by_text_like(self, text: str) -> Claim | None:
        pattern = f"%{text}%"
        with self._get_conn() as conn:
            row = conn.execute(
                sa.select(claims).where(
                    sa.or_(
                        claims.c.claimer_name.ilike(pattern),
                        claims.c.policy_number.ilike(pattern),
                        claims.c.plate.ilike(pattern),
                    )
                )
            ).fetchone()
        return self._row_to_claim(row) if row else None
