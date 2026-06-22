"""List documents by entity type and ID."""

from uuid import UUID

from src.domain.models.entities import Document
from src.domain.ports.repositories import DocumentRepoPort


class ObtenerDocumentos:
    def __init__(self, doc_repo: DocumentRepoPort):
        self._doc_repo = doc_repo

    def by_entity(self, entity_type: str, entity_id: UUID) -> list[Document]:
        if entity_type == "claim":
            return self._doc_repo.get_by_claim_id(entity_id)
        elif entity_type == "group_claim":
            return self._doc_repo.get_by_group_id(entity_id)
        elif entity_type == "invoice":
            doc = self._doc_repo.get_by_billing_id(entity_id)
            return [doc] if doc else []
        else:
            return []
