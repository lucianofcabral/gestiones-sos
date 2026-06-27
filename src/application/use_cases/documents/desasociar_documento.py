"""DesasociarDocumento — remove the link between a document and an entity.

The document and its file remain in storage; only the entity association is removed.
"""

from uuid import UUID

from src.domain.ports.repositories import DocumentRepoPort


class DesasociarDocumento:
    """Remove a document-entity link without deleting the document or its file."""

    def __init__(self, doc_repo: DocumentRepoPort) -> None:
        self._doc_repo = doc_repo

    def execute(
        self, document_id: UUID, entity_type: str, entity_id: UUID
    ) -> None:
        self._doc_repo.remove_document_entity(document_id, entity_type, entity_id)
