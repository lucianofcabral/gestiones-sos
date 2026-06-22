from contextlib import contextmanager
from typing import Any
from uuid import UUID

import sqlalchemy as sa

from src.domain.models.entities import PaymentVia
from src.infrastructure.database.connection import get_connection
from src.infrastructure.database.tables import payment_vias


class SqlAlchemyPaymentViaRepository:
    """Implementación de PaymentViaRepoPort usando SQLAlchemy Core."""

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
    def _row_to_entity(row: sa.Row) -> PaymentVia:
        return PaymentVia(
            payment_via_id=row.payment_via_id,
            name=row.name,
            active=row.active,
            created_at=row.created_at,
        )

    # ── BaseRepo ──────────────────────────────────────────────────────────────

    def add(self, model: PaymentVia) -> PaymentVia:
        with self._get_conn() as conn:
            conn.execute(
                sa.insert(payment_vias).values(
                    payment_via_id=model.payment_via_id,
                    name=model.name,
                    active=model.active,
                    created_at=model.created_at,
                )
            )
        return model

    def get_by_id(self, id: UUID) -> PaymentVia | None:
        with self._get_conn() as conn:
            row = conn.execute(
                sa.select(payment_vias).where(payment_vias.c.payment_via_id == id)
            ).fetchone()
        return self._row_to_entity(row) if row else None

    def delete(self, id: UUID) -> None:
        with self._get_conn() as conn:
            conn.execute(
                sa.delete(payment_vias).where(payment_vias.c.payment_via_id == id)
            )

    def update(self, id: UUID, model: PaymentVia) -> bool:
        with self._get_conn() as conn:
            result = conn.execute(
                sa.update(payment_vias)
                .where(payment_vias.c.payment_via_id == id)
                .values(
                    name=model.name,
                    active=model.active,
                )
            )
        return result.rowcount > 0

    def get_all(self) -> list[PaymentVia]:
        with self._get_conn() as conn:
            rows = conn.execute(sa.select(payment_vias)).fetchall()
        return [self._row_to_entity(r) for r in rows]

    def exists(self, data: dict[str, Any]) -> bool:
        conditions = [payment_vias.c[k] == v for k, v in data.items()]
        with self._get_conn() as conn:
            row = conn.execute(
                sa.select(payment_vias.c.payment_via_id).where(sa.and_(*conditions))
            ).fetchone()
        return row is not None

    def get_by_ids(self, ids: list[UUID]) -> list[PaymentVia]:
        with self._get_conn() as conn:
            rows = conn.execute(
                sa.select(payment_vias).where(payment_vias.c.payment_via_id.in_(ids))
            ).fetchall()
        return [self._row_to_entity(r) for r in rows]

    # ── PaymentViaRepoPort ────────────────────────────────────────────────────

    def get_by_name(self, name: str) -> PaymentVia | None:
        with self._get_conn() as conn:
            row = conn.execute(
                sa.select(payment_vias).where(payment_vias.c.name == name)
            ).fetchone()
        return self._row_to_entity(row) if row else None

    def get_transferencia(self) -> PaymentVia | None:
        return self.get_by_name("Transferencia")

    def get_nc(self) -> PaymentVia | None:
        return self.get_by_name("Nota de Crédito")

    # ── _Activatable ──────────────────────────────────────────────────────────

    def activate(self, id: UUID) -> bool:
        return self.update(id, PaymentVia(payment_via_id=id, active=True))

    def inactivate(self, id: UUID) -> bool:
        return self.update(id, PaymentVia(payment_via_id=id, active=False))
