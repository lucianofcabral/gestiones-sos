from contextlib import contextmanager
from typing import Any
from uuid import UUID

import sqlalchemy as sa

from src.domain.models.entities import Period
from src.infrastructure.database.connection import get_connection
from src.infrastructure.database.tables import invoices as inv_tbl
from src.infrastructure.database.tables import periods


class SqlAlchemyPeriodRepository:
    """Implementación de PeriodRepoPort usando SQLAlchemy Core.

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
    def _row_to_period(row: sa.Row) -> Period:
        return Period(
            period_id=row.period_id,
            year=row.year,
            month=row.month,
            created_at=row.created_at,
        )

    # ── BaseRepo ──────────────────────────────────────────────────────────────

    def add(self, model: Period) -> Period:
        with self._get_conn() as conn:
            conn.execute(
                sa.insert(periods).values(
                    period_id=model.period_id,
                    year=model.year,
                    month=model.month,
                    created_at=model.created_at,
                )
            )
        return model

    def get_by_id(self, id: UUID) -> Period | None:
        with self._get_conn() as conn:
            row = conn.execute(
                sa.select(periods).where(periods.c.period_id == id)
            ).fetchone()
        return self._row_to_period(row) if row else None

    def delete(self, id: UUID) -> None:
        with self._get_conn() as conn:
            conn.execute(sa.delete(periods).where(periods.c.period_id == id))

    def update(self, id: UUID, model: Period) -> bool:
        with self._get_conn() as conn:
            result = conn.execute(
                sa.update(periods)
                .where(periods.c.period_id == id)
                .values(
                    year=model.year,
                    month=model.month,
                )
            )
        return result.rowcount > 0

    def get_all(self) -> list[Period]:
        with self._get_conn() as conn:
            rows = conn.execute(sa.select(periods)).fetchall()
        return [self._row_to_period(r) for r in rows]

    def exists(self, data: dict[str, Any]) -> bool:
        conditions = [periods.c[k] == v for k, v in data.items()]
        with self._get_conn() as conn:
            row = conn.execute(
                sa.select(periods.c.period_id).where(sa.and_(*conditions))
            ).fetchone()
        return row is not None

    def get_by_ids(self, ids: list[UUID]) -> list[Period]:
        with self._get_conn() as conn:
            rows = conn.execute(
                sa.select(periods).where(periods.c.period_id.in_(ids))
            ).fetchall()
        return [self._row_to_period(r) for r in rows]

    # ── PeriodRepoPort ────────────────────────────────────────────────────────

    def get_by_year_month(self, year: int, month: int) -> Period | None:
        with self._get_conn() as conn:
            row = conn.execute(
                sa.select(periods).where(
                    sa.and_(periods.c.year == year, periods.c.month == month)
                )
            ).fetchone()
        return self._row_to_period(row) if row else None

    def get_n_last(self, n: int | None) -> list[Period]:
        stmt = sa.select(periods).order_by(
            periods.c.year.desc(), periods.c.month.desc()
        )
        if n is not None:
            stmt = stmt.limit(n)
        with self._get_conn() as conn:
            rows = conn.execute(stmt).fetchall()
        return [self._row_to_period(r) for r in rows]

    def get_total_billing_by_year_month(self, year: int, month: int) -> float:
        with self._get_conn() as conn:
            row = conn.execute(
                sa.select(sa.func.coalesce(sa.func.sum(inv_tbl.c.amount), 0))
                .select_from(
                    periods.join(inv_tbl, periods.c.period_id == inv_tbl.c.period_id)
                )
                .where(sa.and_(periods.c.year == year, periods.c.month == month))
            ).scalar()
        return float(row)
