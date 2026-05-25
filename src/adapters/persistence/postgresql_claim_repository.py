from typing import Any
from uuid import UUID

import sqlalchemy as sa

from src.domain.models.entities import Claim
from src.infrastructure.database.connection import get_connection
from src.infrastructure.database.tables import claims


class PostgreSQLClaimRepository:
    """Implementación de ClaimRepoPort usando SQLAlchemy Core + PostgreSQL."""

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
        with get_connection() as conn:
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
            conn.commit()
        return model

    def get_by_id(self, id: UUID) -> Claim | None:
        with get_connection() as conn:
            row = conn.execute(
                sa.select(claims).where(claims.c.claim_id == id)
            ).fetchone()
        return self._row_to_claim(row) if row else None

    def delete(self, id: UUID) -> None:
        with get_connection() as conn:
            conn.execute(sa.delete(claims).where(claims.c.claim_id == id))
            conn.commit()

    def update(self, id: UUID, model: Claim) -> bool:
        with get_connection() as conn:
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
            conn.commit()
        return result.rowcount > 0

    def get_all(self) -> list[Claim]:
        with get_connection() as conn:
            rows = conn.execute(sa.select(claims)).fetchall()
        return [self._row_to_claim(r) for r in rows]

    def exists(self, data: dict[str, Any]) -> bool:
        conditions = [claims.c[k] == v for k, v in data.items()]
        with get_connection() as conn:
            row = conn.execute(
                sa.select(claims.c.claim_id).where(sa.and_(*conditions))
            ).fetchone()
        return row is not None

    def get_by_ids(self, ids: list[UUID]) -> list[Claim]:
        with get_connection() as conn:
            rows = conn.execute(
                sa.select(claims).where(claims.c.claim_id.in_(ids))
            ).fetchall()
        return [self._row_to_claim(r) for r in rows]

    # ── _Activatable ──────────────────────────────────────────────────────────

    def activate(self, id: UUID) -> bool:
        with get_connection() as conn:
            result = conn.execute(
                sa.update(claims).where(claims.c.claim_id == id).values(active=True)
            )
            conn.commit()
        return result.rowcount > 0

    def inactivate(self, id: UUID) -> bool:
        with get_connection() as conn:
            result = conn.execute(
                sa.update(claims).where(claims.c.claim_id == id).values(active=False)
            )
            conn.commit()
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
        with get_connection() as conn:
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
