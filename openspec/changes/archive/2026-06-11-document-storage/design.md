# Design: Document Storage

## Technical Approach

Content-addressable filesystem storage with SHA-256 hashing and 2-level directory nesting. Documents are domain entities persisted via a new `documents` + `document_entities` SQLAlchemy Core table pair. The storage service is a pure infrastructure concern; the document repo and use cases follow existing patterns exactly. File serving uses a NiceGUI `@ui.page` with auth guard that reads from disk and returns the file with correct MIME.

## Architecture Decisions

### Decision: Filesystem over S3/MinIO

| Option | Storage | Operations | Complexity |
|--------|---------|------------|------------|
| **Filesystem** (chosen) | Simple path I/O | sync `open()`/`shutil` | Zero infra |
| MinIO/S3 | Object storage | boto3/S3 client | Auth, bucket config |
| DB BLOB | No FS to manage | Single DB | Bloat, no dedup, slow |

**Rationale**: ~5000 docs, single-instance deployment. Filesystem is zero-infra. If scale demands S3 later, `StoragePort` abstraction makes it a drop-in replacement.

### Decision: SHA-256 with 2-level nesting

**Choice**: `{hash[:2]}/{hash[2:4]}/{hash}.{ext}` — ~65K directories at level 1, ~4B at level 2. **Rationale**: Prevents any single directory from accumulating too many entries (ext4 dir limits). Extension from original filename keeps it human-readable. SHA-256 provides automatic dedup at this scale (collision risk: negligible).

### Decision: Extension from filename, not MIME

**Rationale**: The original extension is what users expect in downloads. MIME is stored for `Content-Type` headers but the file extension comes from the original upload name.

### Decision: NiceGUI custom page for file serving (not static files)

**Rationale**: `app.add_static_files()` bypasses auth. A `@ui.page("/api/documents/{id}/file")` with `AppShell` auth guard (via token check) ensures only authenticated users access files. Returns `media_type` from stored MIME and `Content-Disposition` with original filename.

## Data Flow

### Upload

```
User → UploadForm (NiceGUI)
  → SubirDocumento.execute(input)
    → validate_type() + validate_size()   [reject 400/413]
    → SHA-256(bytes).hexdigest()
    → storage_service.store(hash, ext, bytes)   [skips if exists]
    → doc_repo.add(Document{...})               [metadata]
    → document_entities_repo.add(DocumentEntity{...}) [if linked]
  → return document_id
```

### Download

```
User → /api/documents/{id}/file
  → auth check (AppShell token)
  → doc_repo.get_by_id(id)          [404 if missing]
  → storage_service.retrieve(hash)  [404 if missing on disk]
  → Return FileResponse with media_type, Content-Disposition
```

## File Changes

| File | Action |
|------|--------|
| `src/domain/models/entities.py` | Modify Document entity (add fields, tighten hash) |
| `src/domain/ports/repositories.py` | Already defined — no changes |
| `src/infrastructure/database/tables.py` | Add `documents`, `document_entities` tables |
| `src/infrastructure/storage/__init__.py` | Create (empty) |
| `src/infrastructure/storage/filesystem_storage.py` | Create FilesystemStorageService |
| `src/adapters/persistence/sqlalchemy_document_repository.py` | Create SqlAlchemyDocumentRepository |
| `src/adapters/persistence/inmemory_document_repository.py` | Create InMemoryDocumentRepository |
| `src/application/use_cases/documents/__init__.py` | Create (empty) |
| `src/application/use_cases/documents/subir_documento.py` | Create SubirDocumento use case |
| `src/application/use_cases/documents/obtener_documentos.py` | Create ObtenerDocumentos use case |
| `src/application/use_cases/documents/descargar_documento.py` | Create DescargarDocumento use case |
| `src/ui/pages/documentos.py` | Create document gallery page |
| `src/ui/components/document_upload.py` | Create reusable upload component |
| `src/infrastructure/container.py` | Wire storage, repo, use cases |
| `alembic/versions/{rev}_create_document_tables.py` | Create migration |
| `tests/test_documents.py` | Create tests |

## Interfaces / Contracts

### FilesystemStorageService

```python
class FilesystemStorageService:
    def __init__(self, base_path: str = "./storage/documents") -> None: ...

    def store(self, hash: str, ext: str, content: bytes) -> str:
        """Write to {hash[:2]}/{hash[2:4]}/{hash}.{ext}. No-op if exists."""

    def retrieve(self, hash: str) -> bytes | None:
        """Read file by hash. Returns None if missing."""

    def delete(self, hash: str) -> None:
        """Remove file from disk. No-op if missing."""

    def exists(self, hash: str) -> bool: ...
```

### Use Cases

```python
class SubirDocumento:
    def execute(self, input: SubirDocumentoInput) -> SubirDocumentoOutput: ...

class ObtenerDocumentos:
    def by_entity(self, entity_type: str, entity_id: UUID) -> list[Document]: ...

class DescargarDocumento:
    def execute(self, document_id: UUID) -> DocumentoFile: ...
```

### SubirDocumentoInput (Pydantic)

| Field | Type | Required |
|-------|------|----------|
| `filename` | `str` | Yes |
| `content` | `bytes` | Yes (file bytes) |
| `mime` | `str` | Yes |
| `description` | `str` | No (default `""`) |
| `uploaded_by` | `UUID` | Yes |
| `entity_type` | `str \| None` | No |
| `entity_id` | `UUID \| None` | No |

## Testing Strategy

| Layer | What | How |
|-------|------|-----|
| Storage | store/retrieve/delete/exists, dedup (same hash=no second write), missing file → None | Fixture with `tempfile.TemporaryDirectory` |
| In-memory repo | BaseRepo contract + `get_by_content`, `get_by_name`, entity queries | InMemoryDocumentRepository + seed helpers |
| Upload use case | valid/invalid types, size limit, dedup, entity linkage | InMemoryDocumentRepo + TempDir storage |
| Download use case | existing/missing file/metadata, auth | Mock repo + storage |
| Gallery | entity query → empty/populated list | InMemoryDoc repo, verify sort order |

## Migration / Rollout

No data migration required. Alembic revision adds `documents` and `document_entities` tables. Storage directory created on first use (lazy). Rollback: `alembic downgrade -1`, delete storage dir.

## Open Questions

- None
