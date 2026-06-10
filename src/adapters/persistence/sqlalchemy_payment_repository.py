from contextlib import contextmanager
from datetime import datetime
from typing import Any
from uuid import UUID

import sqlalchemy as sa

from src.domain.models.entities import Payment
from src.infrastructure.database.connection import get_connection
from src.infrastructure.database.tables import payments


class SqlAlchemyPaymentRepository:
    """Implementación de PaymentRepoPort usando SQLAlchemy Core.

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
    def _row_to_payment(row: sa.Row) -> Payment:
        return Payment(
            payment_id=row.payment_id,
            claim_id=row.claim_id,
            payer_id=row.payer_id,
            payee_id=row.payee_id,
            payment_via_id=row.payment_via_id,
            amount=float(row.amount),
            active=row.active,
            created_date=row.created_date,
        )

    # ── BaseRepo ──────────────────────────────────────────────────────────────

    def add(self, model: Payment) -> Payment:
        with self._get_conn() as conn:
            conn.execute(
                sa.insert(payments).values(
                    payment_id=model.payment_id,
                    claim_id=model.claim_id,
                    payer_id=model.payer_id,
                    payee_id=model.payee_id,
                    payment_via_id=model.payment_via_id,
                    amount=model.amount,
                    active=model.active,
                    created_date=model.created_date,
                )
            )
        return model

    def get_by_id(self, id: UUID) -> Payment | None:
        with self._get_conn() as conn:
            row = conn.execute(
                sa.select(payments).where(payments.c.payment_id == id)
            ).fetchone()
        return self._row_to_payment(row) if row else None

    def delete(self, id: UUID) -> None:
        with self._get_conn() as conn:
            conn.execute(sa.delete(payments).where(payments.c.payment_id == id))

    def update(self, id: UUID, model: Payment) -> bool:
        with self._get_conn() as conn:
            result = conn.execute(
                sa.update(payments)
                .where(payments.c.payment_id == id)
                .values(
                    claim_id=model.claim_id,
                    payer_id=model.payer_id,
                    payee_id=model.payee_id,
                    payment_via_id=model.payment_via_id,
                    amount=model.amount,
                    active=model.active,
                    created_date=model.created_date,
                )
            )
        return result.rowcount > 0

    def get_all(self) -> list[Payment]:
        with self._get_conn() as conn:
            rows = conn.execute(sa.select(payments)).fetchall()
        return [self._row_to_payment(r) for r in rows]

    def exists(self, data: dict[str, Any]) -> bool:
        conditions = [payments.c[k] == v for k, v in data.items()]
        with self._get_conn() as conn:
            row = conn.execute(
                sa.select(payments.c.payment_id).where(sa.and_(*conditions))
            ).fetchone()
        return row is not None

    def get_by_ids(self, ids: list[UUID]) -> list[Payment]:
        with self._get_conn() as conn:
            rows = conn.execute(
                sa.select(payments).where(payments.c.payment_id.in_(ids))
            ).fetchall()
        return [self._row_to_payment(r) for r in rows]

    # ── _Activatable ──────────────────────────────────────────────────────────

    def activate(self, id: UUID) -> bool:
        with self._get_conn() as conn:
            result = conn.execute(
                sa.update(payments)
                .where(payments.c.payment_id == id)
                .values(active=True)
            )
        return result.rowcount > 0

    def inactivate(self, id: UUID) -> bool:
        with self._get_conn() as conn:
            result = conn.execute(
                sa.update(payments)
                .where(payments.c.payment_id == id)
                .values(active=False)
            )
        return result.rowcount > 0

    # ── PaymentRepoPort extra ─────────────────────────────────────────────────

    def deleteable(self, id: UUID) -> bool:
        # Sin verificación de NcPayment en SQLAlchemy: siempre permitido
        return True

    def inactivatable(self, id: UUID) -> bool:
        # Sin verificación de NcPayment en SQLAlchemy: siempre permitido
        return True

    def get_by_claim_id(self, claim_id: UUID) -> list[Payment]:
        with self._get_conn() as conn:
            rows = conn.execute(
                sa.select(payments).where(payments.c.claim_id == claim_id)
            ).fetchall()
        return [self._row_to_payment(r) for r in rows]

    def get_by_date_range(self, start_date: str, end_date: str) -> list[Payment]:
        start = datetime.fromisoformat(start_date)
        end = datetime.fromisoformat(end_date)
        with self._get_conn() as conn:
            rows = conn.execute(
                sa.select(payments).where(
                    sa.and_(
                        payments.c.created_date >= start, payments.c.created_date <= end
                    )
                )
            ).fetchall()
        return [self._row_to_payment(r) for r in rows]

    def get_by_amount_range(
        self, min_amount: float, max_amount: float
    ) -> list[Payment]:
        with self._get_conn() as conn:
            rows = conn.execute(
                sa.select(payments).where(
                    sa.and_(
                        payments.c.amount >= min_amount, payments.c.amount <= max_amount
                    )
                )
            ).fetchall()
        return [self._row_to_payment(r) for r in rows]
