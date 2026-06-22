"""Upload a document — save file, compute hash, persist metadata, link to entity."""

from dataclasses import dataclass
from uuid import UUID, uuid4

from src.domain.models.entities import Document
from src.domain.ports.repositories import DocumentRepoPort
from src.infrastructure.storage.filesystem_storage import FilesystemStorageService


@dataclass
class SubirDocumentoInput:
    content: bytes
    name: str
    mime: str
    type: str
    entity_type: str
    entity_id: UUID
    description: str = ""
    uploaded_by: UUID | None = None


@dataclass
class SubirDocumentoOutput:
    document_id: UUID


class SubirDocumento:
    def __init__(
        self,
        doc_repo: DocumentRepoPort,
        storage: FilesystemStorageService,
    ):
        self._doc_repo = doc_repo
        self._storage = storage

    def execute(self, input: SubirDocumentoInput) -> SubirDocumentoOutput:
        ext = input.name.rsplit(".", 1)[-1] if "." in input.name else ""

        # Save to filesystem (no-op if hash already exists)
        hash = self._storage.save(input.content, ext)

        # Dedup: check if content with same hash already exists
        existing = self._doc_repo.get_by_content(input.content)
        if existing:
            return SubirDocumentoOutput(document_id=existing.document_id)

        doc = Document(
            document_id=uuid4(),
            document_hash=hash,
            type=input.type,
            name=input.name,
            size=len(input.content),
            mime=input.mime,
            description=input.description,
            uploaded_by=input.uploaded_by,
        )
        self._doc_repo.add(doc)
        self._doc_repo.add_document_entity(
            doc.document_id, input.entity_type, input.entity_id
        )
        return SubirDocumentoOutput(document_id=doc.document_id)
