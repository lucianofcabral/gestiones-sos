from contextlib import contextmanager
from typing import Any
from uuid import UUID

import sqlalchemy as sa

from src.domain.models.entities import Invoice
from src.infrastructure.database.connection import get_connection
from src.infrastructure.database.tables import invoices


class SqlAlchemyBillingRepository:
    """Implementación de BillingRepoPort usando SQLAlchemy Core."""

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
    def _row_to_entity(row: sa.Row) -> Invoice:
        return Invoice(
            invoice_id=row.invoice_id,
            invoice_number=row.invoice_number,
            period_id=row.period_id,
            emited_date=row.emited_date,
            amount=float(row.amount),
            created_at=row.created_at,
        )

    # ── BaseRepo ──────────────────────────────────────────────────────────────

    def add(self, model: Invoice) -> Invoice:
        with self._get_conn() as conn:
            conn.execute(
                sa.insert(invoices).values(
                    invoice_id=model.invoice_id,
                    invoice_number=model.invoice_number,
                    period_id=model.period_id,
                    emited_date=model.emited_date,
                    amount=model.amount,
                    created_at=model.created_at,
                )
            )
        return model

    def get_by_id(self, id: UUID) -> Invoice | None:
        with self._get_conn() as conn:
            row = conn.execute(
                sa.select(invoices).where(invoices.c.invoice_id == id)
            ).fetchone()
        return self._row_to_entity(row) if row else None

    def delete(self, id: UUID) -> None:
        with self._get_conn() as conn:
            conn.execute(sa.delete(invoices).where(invoices.c.invoice_id == id))

    def update(self, id: UUID, model: Invoice) -> bool:
        with self._get_conn() as conn:
            result = conn.execute(
                sa.update(invoices)
                .where(invoices.c.invoice_id == id)
                .values(
                    invoice_number=model.invoice_number,
                    period_id=model.period_id,
                    emited_date=model.emited_date,
                    amount=model.amount,
                )
            )
        return result.rowcount > 0

    def get_all(self) -> list[Invoice]:
        with self._get_conn() as conn:
            rows = conn.execute(
                sa.select(invoices).order_by(invoices.c.created_at.desc())
            ).fetchall()
        return [self._row_to_entity(r) for r in rows]

    def exists(self, data: dict[str, Any]) -> bool:
        conditions = [invoices.c[k] == v for k, v in data.items()]
        with self._get_conn() as conn:
            row = conn.execute(
                sa.select(invoices.c.invoice_id).where(sa.and_(*conditions))
            ).fetchone()
        return row is not None

    def get_by_ids(self, ids: list[UUID]) -> list[Invoice]:
        with self._get_conn() as conn:
            rows = conn.execute(
                sa.select(invoices).where(invoices.c.invoice_id.in_(ids))
            ).fetchall()
        return [self._row_to_entity(r) for r in rows]

    # ── BillingRepoPort ───────────────────────────────────────────────────────

    def get_by_period_id(self, period_id: UUID) -> list[Invoice]:
        with self._get_conn() as conn:
            rows = conn.execute(
                sa.select(invoices).where(invoices.c.period_id == period_id)
            ).fetchall()
        return [self._row_to_entity(r) for r in rows]

    # ── _DocReachable stubs ──────────────────────────────────────────────────

    def get_by_document_id(self, document_id: UUID) -> list[Invoice]:
        return []

    def get_by_document(self, document: bytes) -> list[Invoice]:
        return []
