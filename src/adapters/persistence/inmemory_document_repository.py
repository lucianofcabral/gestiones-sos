import hashlib
from typing import Any
from uuid import UUID

from src.domain.models.entities import Document


class InMemoryDocumentRepository:
    def __init__(self) -> None:
        self._store: list[Document] = []
        self._entity_store: list[dict[str, Any]] = []

    # ── BaseRepo ──────────────────────────────────────────────────────────────

    def add(self, model: Document) -> Document:
        self._store.append(model)
        return model

    def get_by_id(self, id: UUID) -> Document | None:
        return next((d for d in self._store if d.document_id == id), None)

    def delete(self, id: UUID) -> None:
        self._store = [d for d in self._store if d.document_id != id]

    def update(self, id: UUID, model: Document) -> bool:
        for i, doc in enumerate(self._store):
            if doc.document_id == id:
                self._store[i] = model
                return True
        return False

    def get_all(self) -> list[Document]:
        return list(self._store)

    def exists(self, data: dict[str, Any]) -> bool:
        return any(
            all(getattr(d, k) == v for k, v in data.items()) for d in self._store
        )

    def get_by_ids(self, ids: list[UUID]) -> list[Document]:
        return [d for d in self._store if d.document_id in ids]

    # ── DocumentRepoPort ──────────────────────────────────────────────────────

    def get_by_content(self, content: bytes) -> Document | None:
        hash = hashlib.sha256(content).hexdigest()
        return next((d for d in self._store if d.document_hash == hash), None)

    def get_by_name(self, name: str) -> Document | None:
        return next((d for d in self._store if d.name == name), None)

    def _get_by_entity(self, entity_type: str, entity_id: UUID) -> list[Document]:
        doc_ids = [
            e["document_id"]
            for e in self._entity_store
            if e["entity_type"] == entity_type and e["entity_id"] == entity_id
        ]
        return [d for d in self._store if d.document_id in doc_ids]

    def get_by_claim_id(self, claim_id: UUID) -> list[Document]:
        return self._get_by_entity("claim", claim_id)

    def get_by_group_id(self, group_id: UUID) -> list[Document]:
        return self._get_by_entity("group_claim", group_id)

    def get_by_billing_id(self, billing_id: UUID) -> Document | None:
        docs = self._get_by_entity("invoice", billing_id)
        return docs[0] if docs else None

    # ── DocumentEntity helpers ────────────────────────────────────────────────

    def add_document_entity(
        self, document_id: UUID, entity_type: str, entity_id: UUID
    ) -> None:
        self._entity_store.append(
            {
                "document_id": document_id,
                "entity_type": entity_type,
                "entity_id": entity_id,
            }
        )

    def get_document_entities(self, document_id: UUID) -> list[dict[str, Any]]:
        return [e for e in self._entity_store if e["document_id"] == document_id]
