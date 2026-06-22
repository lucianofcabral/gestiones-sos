"""Tests for document storage: FilesystemStorageService, InMemoryDocumentRepository, SubirDocumento."""

import os
import tempfile
from pathlib import Path
from uuid import UUID, uuid4

import pytest

from src.adapters.persistence.inmemory_document_repository import (
    InMemoryDocumentRepository,
)
from src.application.use_cases.documents.subir_documento import (
    SubirDocumento,
    SubirDocumentoInput,
    SubirDocumentoOutput,
)
from src.domain.models.entities import Document
from src.infrastructure.storage.filesystem_storage import FilesystemStorageService


# ═══════════════════════════════════════════════════════════════════
# 8.1 — FilesystemStorageService
# ═══════════════════════════════════════════════════════════════════


@pytest.fixture
def storage() -> FilesystemStorageService:
    tmp = tempfile.TemporaryDirectory()
    svc = FilesystemStorageService(base_path=tmp.name)
    yield svc
    tmp.cleanup()


class TestFilesystemStorageService:
    def test_save_returns_hash_and_creates_file(
        self, storage: FilesystemStorageService
    ) -> None:
        content = b"hello world"
        ext = "txt"

        hash = storage.save(content, ext)

        assert isinstance(hash, str)
        assert len(hash) == 64  # SHA-256 hex
        assert Path(storage._path_from_hash(hash, ext)).exists()

    def test_save_uses_two_level_nesting(
        self, storage: FilesystemStorageService
    ) -> None:
        content = b"nesting test"
        ext = "pdf"

        hash = storage.save(content, ext)
        path = storage._path_from_hash(hash, ext)

        # Path should be {base}/{hash[:2]}/{hash[2:4]}/{hash}.{ext}
        assert path.parent.name == hash[2:4]
        assert path.parent.parent.name == hash[:2]

    def test_save_same_content_twice_does_not_overwrite(
        self, storage: FilesystemStorageService
    ) -> None:
        content = b"dedup content"
        ext = "txt"

        hash1 = storage.save(content, ext)
        hash2 = storage.save(content, ext)

        assert hash1 == hash2  # same hash = same content
        # File should exist once
        path = storage._path_from_hash(hash1, ext)
        assert path.exists()
        assert path.read_bytes() == content

    def test_get_returns_content(self, storage: FilesystemStorageService) -> None:
        content = b"get me"
        ext = "txt"
        hash = storage.save(content, ext)

        retrieved = storage.get(hash, ext)

        assert retrieved == content

    def test_get_raises_on_missing_file(
        self, storage: FilesystemStorageService
    ) -> None:
        with pytest.raises(FileNotFoundError):
            storage.get(
                "0000000000000000000000000000000000000000000000000000000000000000",
                "txt",
            )

    def test_delete_removes_file(self, storage: FilesystemStorageService) -> None:
        content = b"delete me"
        ext = "txt"
        hash = storage.save(content, ext)
        path = storage._path_from_hash(hash, ext)
        assert path.exists()

        storage.delete(hash, ext)

        assert not path.exists()

    def test_delete_nonexistent_does_not_raise(
        self, storage: FilesystemStorageService
    ) -> None:
        storage.delete(
            "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa", "txt"
        )

    def test_exists_returns_true_when_file_exists(
        self, storage: FilesystemStorageService
    ) -> None:
        content = b"exists check"
        ext = "txt"
        hash = storage.save(content, ext)

        assert storage.exists(hash, ext) is True

    def test_exists_returns_false_when_missing(
        self, storage: FilesystemStorageService
    ) -> None:
        assert (
            storage.exists(
                "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
                "txt",
            )
            is False
        )

    def test_base_path_configurable(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            custom_base = os.path.join(tmp, "custom", "path")
            svc = FilesystemStorageService(base_path=custom_base)
            hash = svc.save(b"configurable", "txt")
            path = svc._path_from_hash(hash, "txt")
            assert path.exists()
            assert str(path).startswith(custom_base)

    def test_base_path_from_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            monkeypatch.setenv("DOCUMENTS_STORAGE_PATH", tmp)
            svc = FilesystemStorageService()
            hash = svc.save(b"env path", "txt")
            path = svc._path_from_hash(hash, "txt")
            assert path.exists()
            assert str(path).startswith(tmp)

    def test_different_contents_produce_different_hashes(
        self, storage: FilesystemStorageService
    ) -> None:
        h1 = storage.save(b"alpha", "txt")
        h2 = storage.save(b"beta", "txt")
        assert h1 != h2

    def test_ext_preserved_in_filename(self, storage: FilesystemStorageService) -> None:
        content = b"ext test"
        hash = storage.save(content, "pdf")
        path = storage._path_from_hash(hash, "pdf")
        assert path.suffix == ".pdf"

    def test_directory_created_on_first_save(
        self, storage: FilesystemStorageService
    ) -> None:
        content = b"dir create"
        hash = storage.save(content, "txt")
        path = storage._path_from_hash(hash, "txt")
        assert path.parent.exists()


# ═══════════════════════════════════════════════════════════════════
# 8.2 — InMemoryDocumentRepository
# ═══════════════════════════════════════════════════════════════════


@pytest.fixture
def doc_repo() -> InMemoryDocumentRepository:
    return InMemoryDocumentRepository()


def _seed_doc(
    repo: InMemoryDocumentRepository,
    name: str = "test.pdf",
    content: bytes | None = None,
    doc_id: UUID | None = None,
) -> Document:
    import hashlib

    content = content or b"seed content"
    hash = hashlib.sha256(content).hexdigest()
    doc = Document(
        document_id=doc_id or uuid4(),
        document_hash=hash,
        type="pdf",
        name=name,
        size=len(content),
        mime="application/pdf",
    )
    repo.add(doc)
    return doc


class TestInMemoryDocumentRepositoryBaseRepo:
    """Verify BaseRepo[Document] contract."""

    def test_add_stores_document(self, doc_repo: InMemoryDocumentRepository) -> None:
        doc = _seed_doc(doc_repo)
        assert doc_repo.get_by_id(doc.document_id) == doc

    def test_get_by_id_returns_none_when_not_found(
        self, doc_repo: InMemoryDocumentRepository
    ) -> None:
        assert doc_repo.get_by_id(uuid4()) is None

    def test_get_all_returns_all(self, doc_repo: InMemoryDocumentRepository) -> None:
        d1 = _seed_doc(doc_repo)
        d2 = _seed_doc(doc_repo)
        result = doc_repo.get_all()
        assert len(result) == 2
        assert d1 in result
        assert d2 in result

    def test_get_all_empty(self, doc_repo: InMemoryDocumentRepository) -> None:
        assert doc_repo.get_all() == []

    def test_exists_returns_true(self, doc_repo: InMemoryDocumentRepository) -> None:
        _seed_doc(doc_repo, name="findme.pdf")
        assert doc_repo.exists({"name": "findme.pdf"}) is True

    def test_exists_returns_false(self, doc_repo: InMemoryDocumentRepository) -> None:
        _seed_doc(doc_repo, name="exists.pdf")
        assert doc_repo.exists({"name": "nope.pdf"}) is False

    def test_update_returns_true_and_modifies(
        self, doc_repo: InMemoryDocumentRepository
    ) -> None:
        doc = _seed_doc(doc_repo, name="old.pdf")
        updated = Document(
            document_id=doc.document_id,
            document_hash=doc.document_hash,
            type=doc.type,
            name="new.pdf",
            size=doc.size,
            mime=doc.mime,
        )
        result = doc_repo.update(doc.document_id, updated)
        assert result is True
        stored = doc_repo.get_by_id(doc.document_id)
        assert stored is not None
        assert stored.name == "new.pdf"

    def test_update_returns_false_when_not_found(
        self, doc_repo: InMemoryDocumentRepository
    ) -> None:
        doc = Document(
            document_id=uuid4(),
            document_hash="a",
            type="pdf",
            name="x.pdf",
            size=1,
            mime="a",
        )
        assert doc_repo.update(doc.document_id, doc) is False

    def test_delete_removes_document(
        self, doc_repo: InMemoryDocumentRepository
    ) -> None:
        doc = _seed_doc(doc_repo)
        doc_repo.delete(doc.document_id)
        assert doc_repo.get_by_id(doc.document_id) is None

    def test_delete_nonexistent_does_nothing(
        self, doc_repo: InMemoryDocumentRepository
    ) -> None:
        doc_repo.delete(uuid4())  # must not raise

    def test_get_by_ids_returns_matching(
        self, doc_repo: InMemoryDocumentRepository
    ) -> None:
        d1 = _seed_doc(doc_repo)
        d2 = _seed_doc(doc_repo)
        d3 = _seed_doc(doc_repo)
        result = doc_repo.get_by_ids([d1.document_id, d3.document_id])
        assert len(result) == 2
        assert d1 in result
        assert d3 in result
        assert d2 not in result

    def test_get_by_ids_returns_empty(
        self, doc_repo: InMemoryDocumentRepository
    ) -> None:
        _seed_doc(doc_repo)
        assert doc_repo.get_by_ids([uuid4(), uuid4()]) == []


class TestInMemoryDocumentRepositoryDocumentPort:
    """Verify DocumentRepoPort-specific methods."""

    def test_get_by_content_returns_matching(
        self, doc_repo: InMemoryDocumentRepository
    ) -> None:
        content = b"unique content"
        doc = _seed_doc(doc_repo, content=content)
        result = doc_repo.get_by_content(content)
        assert result is not None
        assert result.document_id == doc.document_id

    def test_get_by_content_returns_none_when_not_found(
        self, doc_repo: InMemoryDocumentRepository
    ) -> None:
        assert doc_repo.get_by_content(b"nonexistent") is None

    def test_get_by_name_returns_matching(
        self, doc_repo: InMemoryDocumentRepository
    ) -> None:
        doc = _seed_doc(doc_repo, name="specific.pdf")
        result = doc_repo.get_by_name("specific.pdf")
        assert result is not None
        assert result.document_id == doc.document_id

    def test_get_by_name_returns_none_when_not_found(
        self, doc_repo: InMemoryDocumentRepository
    ) -> None:
        assert doc_repo.get_by_name("missing.pdf") is None

    def test_get_by_claim_id(self, doc_repo: InMemoryDocumentRepository) -> None:
        claim_id = uuid4()
        doc = _seed_doc(doc_repo)
        doc_repo.add_document_entity(doc.document_id, "claim", claim_id)
        result = doc_repo.get_by_claim_id(claim_id)
        assert len(result) == 1
        assert result[0].document_id == doc.document_id

    def test_get_by_claim_id_returns_empty(
        self, doc_repo: InMemoryDocumentRepository
    ) -> None:
        assert doc_repo.get_by_claim_id(uuid4()) == []

    def test_get_by_group_id(self, doc_repo: InMemoryDocumentRepository) -> None:
        group_id = uuid4()
        doc = _seed_doc(doc_repo)
        doc_repo.add_document_entity(doc.document_id, "group_claim", group_id)
        result = doc_repo.get_by_group_id(group_id)
        assert len(result) == 1

    def test_get_by_billing_id(self, doc_repo: InMemoryDocumentRepository) -> None:
        billing_id = uuid4()
        doc = _seed_doc(doc_repo)
        doc_repo.add_document_entity(doc.document_id, "invoice", billing_id)
        result = doc_repo.get_by_billing_id(billing_id)
        assert result is not None
        assert result.document_id == doc.document_id

    def test_get_by_billing_id_returns_none(
        self, doc_repo: InMemoryDocumentRepository
    ) -> None:
        assert doc_repo.get_by_billing_id(uuid4()) is None

    def test_get_document_entities(self, doc_repo: InMemoryDocumentRepository) -> None:
        doc = _seed_doc(doc_repo)
        eid = uuid4()
        doc_repo.add_document_entity(doc.document_id, "claim", eid)
        entities = doc_repo.get_document_entities(doc.document_id)
        assert len(entities) == 1
        assert entities[0]["entity_type"] == "claim"
        assert entities[0]["entity_id"] == eid

    def test_get_document_entities_empty(
        self, doc_repo: InMemoryDocumentRepository
    ) -> None:
        assert doc_repo.get_document_entities(uuid4()) == []


# ═══════════════════════════════════════════════════════════════════
# 8.3 — SubirDocumento use case
# ═══════════════════════════════════════════════════════════════════


@pytest.fixture
def subir_use_case() -> tuple[
    SubirDocumento, InMemoryDocumentRepository, FilesystemStorageService
]:
    repo = InMemoryDocumentRepository()
    tmp = tempfile.TemporaryDirectory()
    storage_svc = FilesystemStorageService(base_path=tmp.name)
    use_case = SubirDocumento(repo, storage_svc)
    yield use_case, repo, storage_svc
    tmp.cleanup()


class TestSubirDocumento:
    def test_upload_new_file(
        self,
        subir_use_case: tuple[
            SubirDocumento, InMemoryDocumentRepository, FilesystemStorageService
        ],
    ) -> None:
        use_case, repo, _ = subir_use_case
        entity_id = uuid4()

        result = use_case.execute(
            SubirDocumentoInput(
                content=b"new file content",
                name="report.pdf",
                mime="application/pdf",
                type="pdf",
                entity_type="claim",
                entity_id=entity_id,
                uploaded_by=uuid4(),
            )
        )

        assert isinstance(result, SubirDocumentoOutput)
        assert isinstance(result.document_id, UUID)
        # Verify metadata persisted
        stored = repo.get_by_id(result.document_id)
        assert stored is not None
        assert stored.name == "report.pdf"
        assert stored.mime == "application/pdf"
        assert stored.size == len(b"new file content")

    def test_upload_persists_entity_link(
        self,
        subir_use_case: tuple[
            SubirDocumento, InMemoryDocumentRepository, FilesystemStorageService
        ],
    ) -> None:
        use_case, repo, _ = subir_use_case
        entity_id = uuid4()

        result = use_case.execute(
            SubirDocumentoInput(
                content=b"linked file",
                name="linked.pdf",
                mime="application/pdf",
                type="pdf",
                entity_type="claim",
                entity_id=entity_id,
                uploaded_by=uuid4(),
            )
        )

        entities = repo.get_document_entities(result.document_id)
        assert len(entities) == 1
        assert entities[0]["entity_type"] == "claim"
        assert entities[0]["entity_id"] == entity_id

    def test_upload_same_content_returns_existing_document_id(
        self,
        subir_use_case: tuple[
            SubirDocumento, InMemoryDocumentRepository, FilesystemStorageService
        ],
    ) -> None:
        use_case, repo, storage_svc = subir_use_case
        entity_id = uuid4()
        content = b"duplicate content"

        first = use_case.execute(
            SubirDocumentoInput(
                content=content,
                name="first.pdf",
                mime="application/pdf",
                type="pdf",
                entity_type="claim",
                entity_id=entity_id,
                uploaded_by=uuid4(),
            )
        )

        second = use_case.execute(
            SubirDocumentoInput(
                content=content,
                name="second.pdf",
                mime="application/pdf",
                type="pdf",
                entity_type="claim",
                entity_id=entity_id,
                uploaded_by=uuid4(),
            )
        )

        # Same hash → same document_id returned
        assert second.document_id == first.document_id
        # Only one document in repo
        assert len(repo.get_all()) == 1
        # Storage file only written once
        hash = storage_svc.save(content, "pdf")  # no-op
        assert storage_svc.exists(hash, "pdf")

    def test_upload_with_description(
        self,
        subir_use_case: tuple[
            SubirDocumento, InMemoryDocumentRepository, FilesystemStorageService
        ],
    ) -> None:
        use_case, repo, _ = subir_use_case
        result = use_case.execute(
            SubirDocumentoInput(
                content=b"desc test",
                name="desc.pdf",
                mime="application/pdf",
                type="pdf",
                entity_type="claim",
                entity_id=uuid4(),
                description="A useful document",
                uploaded_by=uuid4(),
            )
        )
        stored = repo.get_by_id(result.document_id)
        assert stored is not None
        assert stored.description == "A useful document"

    def test_upload_with_uploaded_by(
        self,
        subir_use_case: tuple[
            SubirDocumento, InMemoryDocumentRepository, FilesystemStorageService
        ],
    ) -> None:
        use_case, repo, _ = subir_use_case
        user_id = uuid4()
        result = use_case.execute(
            SubirDocumentoInput(
                content=b"user test",
                name="user.pdf",
                mime="application/pdf",
                type="pdf",
                entity_type="claim",
                entity_id=uuid4(),
                uploaded_by=user_id,
            )
        )
        stored = repo.get_by_id(result.document_id)
        assert stored is not None
        assert stored.uploaded_by == user_id

    def test_upload_different_contents_produce_different_ids(
        self,
        subir_use_case: tuple[
            SubirDocumento, InMemoryDocumentRepository, FilesystemStorageService
        ],
    ) -> None:
        use_case, _, _ = subir_use_case
        entity_id = uuid4()
        r1 = use_case.execute(
            SubirDocumentoInput(
                content=b"content alpha",
                name="alpha.pdf",
                mime="application/pdf",
                type="pdf",
                entity_type="claim",
                entity_id=entity_id,
                uploaded_by=uuid4(),
            )
        )
        r2 = use_case.execute(
            SubirDocumentoInput(
                content=b"content beta",
                name="beta.pdf",
                mime="application/pdf",
                type="pdf",
                entity_type="claim",
                entity_id=entity_id,
                uploaded_by=uuid4(),
            )
        )
        assert r1.document_id != r2.document_id

    def test_upload_without_entity_type(
        self,
        subir_use_case: tuple[
            SubirDocumento, InMemoryDocumentRepository, FilesystemStorageService
        ],
    ) -> None:
        """Entity_type must be provided; test empty string behavior."""
        use_case, repo, _ = subir_use_case
        result = use_case.execute(
            SubirDocumentoInput(
                content=b"no entity type",
                name="noentity.pdf",
                mime="application/pdf",
                type="pdf",
                entity_type="",
                entity_id=uuid4(),
                uploaded_by=uuid4(),
            )
        )
        stored = repo.get_by_id(result.document_id)
        assert stored is not None
        # Document was stored even with empty entity_type
        assert stored.name == "noentity.pdf"
