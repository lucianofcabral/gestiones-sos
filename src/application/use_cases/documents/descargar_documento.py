"""Download a document — retrieve metadata and file bytes."""

from dataclasses import dataclass
from uuid import UUID

from src.domain.models.entities import Document
from src.domain.ports.repositories import DocumentRepoPort
from src.infrastructure.storage.filesystem_storage import FilesystemStorageService


@dataclass
class DocumentoFile:
    document: Document
    content: bytes


class DescargarDocumento:
    def __init__(
        self,
        doc_repo: DocumentRepoPort,
        storage: FilesystemStorageService,
    ):
        self._doc_repo = doc_repo
        self._storage = storage

    def execute(self, document_id: UUID) -> DocumentoFile | None:
        doc = self._doc_repo.get_by_id(document_id)
        if doc is None:
            return None

        ext = doc.name.rsplit(".", 1)[-1] if "." in doc.name else ""
        content = self._storage.get(doc.document_hash, ext)
        return DocumentoFile(document=doc, content=content)
