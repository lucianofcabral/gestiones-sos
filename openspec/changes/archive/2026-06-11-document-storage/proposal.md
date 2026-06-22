# Proposal: Document Storage

## Intent

Add filesystem-based document storage for ~5000 documents (.pdf, .jpg, etc.) associated with entities (claims, payments, invoices) via the polymorphic DocumentEntity pattern. Storage is content-addressable via SHA-256 hash, enabling automatic dedup and avoiding DB blob bloat.

## Scope

### In Scope
- Domain: add `description` and `uploaded_by` to Document entity, tighten `document_hash` to max_length=64
- Infrastructure: `FilesystemStorageService` — store/retrieve/delete by SHA-256 hash, 2-level dir nesting
- Infrastructure: `documents` + `document_entities` SQLAlchemy tables + Alembic migration
- Adapters: `SqlAlchemyDocumentRepository` + `InMemoryDocumentRepository`
- Application: document upload use case (validate file, compute hash, save to fs, persist metadata, link to entity)
- UI: NiceGUI upload component + document gallery embedable in entity pages
- UI: Authenticated file serving handler (hash-based URLs)
- Container wiring: storage service + document repo + use case
- Tests: storage service, in-memory repo, upload flow

### Out of Scope
- Legacy system import/migration (separate tool)
- Thumbnails / image preview generation
- Document versioning
- Full-text search within documents
- FK constraints (matching existing codebase pattern)

## Capabilities

### New Capabilities
- `document-storage`: Upload, retrieve, and delete documents linked to polymorphic entities via content-addressable filesystem storage

### Modified Capabilities
- None

## Approach

1. Extend `Document` entity with `description` and `uploaded_by`, tighten `document_hash` to 64 chars
2. `FilesystemStorageService` at configurable path (`DOCUMENTS_STORAGE_PATH`, default `./storage/documents/`); storage path = `{hash[:2]}/{hash[2:4]}/{hash}.{ext}`
3. `SqlAlchemyDocumentRepository` implements `DocumentRepoPort`; `InMemoryDocumentRepository` for tests
4. Upload use case: validate file → compute SHA-256 → store to fs → persist metadata → link via `DocumentEntity`
5. NiceGUI upload dialog + gallery component; file serving via authenticated FastAPI route
6. Alembic migration for new tables

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `src/domain/models/entities.py` | Modified | Add `description`, `uploaded_by` to Document |
| `src/infrastructure/storage/` | New | `FilesystemStorageService` |
| `src/infrastructure/database/tables.py` | New | `documents`, `document_entities` tables |
| `src/adapters/repositories/` | New | SQLAlchemy + InMemory document repos |
| `src/application/use_cases/` | New | Document upload use case |
| `src/ui/` | New | Upload component, gallery, file serving |
| `src/container/` | Modified | Wire new services |
| Alembic migration | New | Add tables |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| SHA-256 collision on 5K docs | Low | Theoretically impossible at this scale |
| File system permissions | Low | Configurable path, document in ops runbook |
| Uploaded filename collisions | Low | Content-addressable — same hash = same file |

## Rollback Plan

1. Remove new Alembic migration (revert)
2. Delete `openspec/changes/document-storage/` (proposal only — no data)
3. If deployed: revert tables via `alembic downgrade -1`, remove storage dir
4. File system cleanup: `rm -rf {storage_path}`

## Dependencies

- `python-multipart` for file upload parsing
- `aiofiles` for async file I/O (if not already present)
- Existing `Document`, `DocumentEntity`, `DocumentRepoPort` domain artifacts

## Success Criteria

- [ ] Document can be uploaded and stored to filesystem at correct hash path
- [ ] Same file uploaded twice returns single storage entry (dedup)
- [ ] Document metadata persisted in `documents` table + linked via `document_entities`
- [ ] Document gallery renders existing documents for an entity
- [ ] File serving returns the file with correct MIME type for authorized users
- [ ] InMemoryDocumentRepository passes DocumentRepoPort contract tests
- [ ] FilesystemStorageService handles missing files gracefully
