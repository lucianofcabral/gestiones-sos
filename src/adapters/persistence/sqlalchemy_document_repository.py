import hashlib
from contextlib import contextmanager
from typing import Any
from uuid import UUID

import sqlalchemy as sa

from src.domain.models.entities import Document
from src.infrastructure.database.connection import get_connection
from src.infrastructure.database.tables import document_entities, documents


class SqlAlchemyDocumentRepository:
    """Implementación de DocumentRepoPort usando SQLAlchemy Core.

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
    def _row_to_document(row: sa.Row) -> Document:
        return Document(
            document_id=row.document_id,
            document_hash=row.hash,
            type=row.type,
            name=row.name,
            size=row.size,
            mime=row.mime,
            description=row.description,
            uploaded_by=row.uploaded_by,
            created_at=row.created_at,
        )

    # ── BaseRepo ──────────────────────────────────────────────────────────────

    def add(self, model: Document) -> Document:
        with self._get_conn() as conn:
            conn.execute(
                sa.insert(documents).values(
                    document_id=model.document_id,
                    hash=model.document_hash,
                    type=model.type,
                    name=model.name,
                    size=model.size,
                    mime=model.mime,
                    description=model.description,
                    uploaded_by=model.uploaded_by,
                    created_at=model.created_at,
                )
            )
        return model

    def get_by_id(self, id: UUID) -> Document | None:
        with self._get_conn() as conn:
            row = conn.execute(
                sa.select(documents).where(documents.c.document_id == id)
            ).fetchone()
        return self._row_to_document(row) if row else None

    def delete(self, id: UUID) -> None:
        with self._get_conn() as conn:
            conn.execute(sa.delete(documents).where(documents.c.document_id == id))

    def update(self, id: UUID, model: Document) -> bool:
        with self._get_conn() as conn:
            result = conn.execute(
                sa.update(documents)
                .where(documents.c.document_id == id)
                .values(
                    hash=model.document_hash,
                    type=model.type,
                    name=model.name,
                    size=model.size,
                    mime=model.mime,
                    description=model.description,
                    uploaded_by=model.uploaded_by,
                )
            )
        return result.rowcount > 0

    def get_all(self) -> list[Document]:
        with self._get_conn() as conn:
            rows = conn.execute(sa.select(documents)).fetchall()
        return [self._row_to_document(r) for r in rows]

    def exists(self, data: dict[str, Any]) -> bool:
        conditions = [documents.c[k] == v for k, v in data.items()]
        with self._get_conn() as conn:
            row = conn.execute(
                sa.select(documents.c.document_id).where(sa.and_(*conditions))
            ).fetchone()
        return row is not None

    def get_by_ids(self, ids: list[UUID]) -> list[Document]:
        with self._get_conn() as conn:
            rows = conn.execute(
                sa.select(documents).where(documents.c.document_id.in_(ids))
            ).fetchall()
        return [self._row_to_document(r) for r in rows]

    # ── DocumentRepoPort ──────────────────────────────────────────────────────

    def get_by_content(self, content: bytes) -> Document | None:
        hash = hashlib.sha256(content).hexdigest()
        with self._get_conn() as conn:
            row = conn.execute(
                sa.select(documents).where(documents.c.hash == hash)
            ).fetchone()
        return self._row_to_document(row) if row else None

    def get_by_name(self, name: str) -> Document | None:
        with self._get_conn() as conn:
            row = conn.execute(
                sa.select(documents).where(documents.c.name == name)
            ).fetchone()
        return self._row_to_document(row) if row else None

    def get_by_claim_id(self, claim_id: UUID) -> list[Document]:
        with self._get_conn() as conn:
            rows = conn.execute(
                sa.select(documents)
                .select_from(
                    documents.join(
                        document_entities,
                        documents.c.document_id == document_entities.c.document_id,
                    )
                )
                .where(
                    sa.and_(
                        document_entities.c.entity_type == "claim",
                        document_entities.c.entity_id == claim_id,
                    )
                )
            ).fetchall()
        return [self._row_to_document(r) for r in rows]

    def get_by_group_id(self, group_id: UUID) -> list[Document]:
        with self._get_conn() as conn:
            rows = conn.execute(
                sa.select(documents)
                .select_from(
                    documents.join(
                        document_entities,
                        documents.c.document_id == document_entities.c.document_id,
                    )
                )
                .where(
                    sa.and_(
                        document_entities.c.entity_type == "group_claim",
                        document_entities.c.entity_id == group_id,
                    )
                )
            ).fetchall()
        return [self._row_to_document(r) for r in rows]

    def get_by_billing_id(self, billing_id: UUID) -> Document | None:
        with self._get_conn() as conn:
            row = conn.execute(
                sa.select(documents)
                .select_from(
                    documents.join(
                        document_entities,
                        documents.c.document_id == document_entities.c.document_id,
                    )
                )
                .where(
                    sa.and_(
                        document_entities.c.entity_type == "invoice",
                        document_entities.c.entity_id == billing_id,
                    )
                )
            ).fetchone()
        return self._row_to_document(row) if row else None

    # ── DocumentEntity helpers ────────────────────────────────────────────────

    def add_document_entity(
        self, document_id: UUID, entity_type: str, entity_id: UUID
    ) -> None:
        with self._get_conn() as conn:
            conn.execute(
                sa.insert(document_entities).values(
                    document_id=document_id,
                    entity_type=entity_type,
                    entity_id=entity_id,
                )
            )

    def get_document_entities(
        self, document_id: UUID
    ) -> list[dict[str, Any]]:
        with self._get_conn() as conn:
            rows = conn.execute(
                sa.select(document_entities).where(
                    document_entities.c.document_id == document_id
                )
            ).fetchall()
        return [
            {
                "document_id": r.document_id,
                "entity_type": r.entity_type,
                "entity_id": r.entity_id,
                "created_at": r.created_at,
            }
            for r in rows
        ]
