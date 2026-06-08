from contextlib import contextmanager
from typing import Any
from uuid import UUID

import sqlalchemy as sa

from src.domain.models.entities import CreditNote
from src.infrastructure.database.connection import get_connection
from src.infrastructure.database.tables import nc_payments


class SqlAlchemyNcPaymentRepository:
    """Implementación de NcPaymentRepoPort usando SQLAlchemy Core.

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
    def _row_to_nc_payment(row: sa.Row) -> CreditNote:
        return CreditNote(
            nc_payment_id=row.nc_payment_id,
            payment_id=row.payment_id,
            period_id=row.period_id,
            delivered=row.delivered,
            active=row.active,
            created_date=row.created_date,
        )

    # ── BaseRepo ──────────────────────────────────────────────────────────────

    def add(self, model: CreditNote) -> CreditNote:
        with self._get_conn() as conn:
            conn.execute(
                sa.insert(nc_payments).values(
                    nc_payment_id=model.nc_payment_id,
                    payment_id=model.payment_id,
                    period_id=model.period_id,
                    delivered=model.delivered,
                    active=model.active,
                    created_date=model.created_date,
                )
            )
        return model

    def get_by_id(self, id: UUID) -> CreditNote | None:
        with self._get_conn() as conn:
            row = conn.execute(
                sa.select(nc_payments).where(nc_payments.c.nc_payment_id == id)
            ).fetchone()
        return self._row_to_nc_payment(row) if row else None

    def delete(self, id: UUID) -> None:
        with self._get_conn() as conn:
            conn.execute(
                sa.delete(nc_payments).where(nc_payments.c.nc_payment_id == id)
            )

    def update(self, id: UUID, model: CreditNote) -> bool:
        with self._get_conn() as conn:
            result = conn.execute(
                sa.update(nc_payments)
                .where(nc_payments.c.nc_payment_id == id)
                .values(
                    payment_id=model.payment_id,
                    period_id=model.period_id,
                    delivered=model.delivered,
                    active=model.active,
                    created_date=model.created_date,
                )
            )
        return result.rowcount > 0

    def get_all(self) -> list[CreditNote]:
        with self._get_conn() as conn:
            rows = conn.execute(sa.select(nc_payments)).fetchall()
        return [self._row_to_nc_payment(r) for r in rows]

    def exists(self, data: dict[str, Any]) -> bool:
        conditions = [nc_payments.c[k] == v for k, v in data.items()]
        with self._get_conn() as conn:
            row = conn.execute(
                sa.select(nc_payments.c.nc_payment_id).where(
                    sa.and_(*conditions)
                )
            ).fetchone()
        return row is not None

    def get_by_ids(self, ids: list[UUID]) -> list[CreditNote]:
        with self._get_conn() as conn:
            rows = conn.execute(
                sa.select(nc_payments).where(
                    nc_payments.c.nc_payment_id.in_(ids)
                )
            ).fetchall()
        return [self._row_to_nc_payment(r) for r in rows]

    # ── _Activatable ──────────────────────────────────────────────────────────

    def activate(self, id: UUID) -> bool:
        with self._get_conn() as conn:
            result = conn.execute(
                sa.update(nc_payments)
                .where(nc_payments.c.nc_payment_id == id)
                .values(active=True)
            )
        return result.rowcount > 0

    def inactivate(self, id: UUID) -> bool:
        with self._get_conn() as conn:
            result = conn.execute(
                sa.update(nc_payments)
                .where(nc_payments.c.nc_payment_id == id)
                .values(active=False)
            )
        return result.rowcount > 0

    # ── NcPaymentRepoPort extra ───────────────────────────────────────────────

    def deleteable(self, id: UUID) -> bool:
        return True

    def mark_delivered(self, id: UUID) -> bool:
        with self._get_conn() as conn:
            result = conn.execute(
                sa.update(nc_payments)
                .where(nc_payments.c.nc_payment_id == id)
                .values(delivered=True)
            )
        return result.rowcount > 0

    def get_by_payment_id(self, payment_id: UUID) -> CreditNote | None:
        with self._get_conn() as conn:
            row = conn.execute(
                sa.select(nc_payments).where(
                    nc_payments.c.payment_id == payment_id
                )
            ).fetchone()
        return self._row_to_nc_payment(row) if row else None

    def get_by_period_id(self, period_id: UUID) -> list[CreditNote]:
        with self._get_conn() as conn:
            rows = conn.execute(
                sa.select(nc_payments).where(
                    nc_payments.c.period_id == period_id
                )
            ).fetchall()
        return [self._row_to_nc_payment(r) for r in rows]
