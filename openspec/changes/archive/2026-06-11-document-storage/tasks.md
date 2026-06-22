# Tasks: Document Storage

## Review Workload Forecast

Decision needed before apply: Yes
Chained PRs recommended: Yes
Chain strategy: pending
400-line budget risk: High

| Field | Value |
|-------|-------|
| Estimated changed lines | ~1000 |
| 400-line budget risk | High |
| Chained PRs recommended | Yes |
| Suggested split | PR1: Domain+Storage+DB → PR2: Repos+UseCases → PR3: UI+Wiring+Tests |
| Delivery strategy | ask-on-risk |
| Chain strategy | pending |

### Suggested Work Units

| Unit | Goal | Likely PR | Notes |
|------|------|-----------|-------|
| 1 | Domain entity, storage service, DB tables + migration | PR 1 | Tests for storage included |
| 2 | SQLAlchemy + InMemory repos, 3 use cases | PR 2 | Tests for repos + SubirDocumento |
| 3 | UI upload component, gallery page, file serving, container wiring, nav | PR 3 | Integration-tested via UI |

## Phase 1: Domain

- [x] 1.1 Add `description: str = ""` and `uploaded_by: UUID \| None = None` to `Document` entity; tighten `document_hash` to `max_length=64`

## Phase 2: Infrastructure — Storage

- [x] 2.1 Create `src/infrastructure/storage/__init__.py` (empty)
- [x] 2.2 Create `src/infrastructure/storage/filesystem_storage.py` with `FilesystemStorageService` — store/retrieve/delete/exists, SHA-256 2-level nesting `{hash[:2]}/{hash[2:4]}/{hash}.{ext}`, configurable base path from `DOCUMENTS_STORAGE_PATH` env var (default `./storage/documents`)

## Phase 3: DB

- [x] 3.1 Add `documents` and `document_entities` tables to `src/infrastructure/database/tables.py`
- [x] 3.2 Create Alembic migration revision for `documents` + `document_entities`

## Phase 4: Repositories

- [x] 4.1 Create `src/adapters/persistence/sqlalchemy_document_repository.py` — `SqlAlchemyDocumentRepository` implementing `BaseRepo[Document]` + `DocumentRepoPort` methods incl. `get_by_content`, `get_by_claim_id`/`get_by_group_id`/`get_by_billing_id` via JOIN on `document_entities`
- [x] 4.2 Create `src/adapters/persistence/inmemory_document_repository.py` — `InMemoryDocumentRepository` following existing in-memory patterns

## Phase 5: Use Cases

- [x] 5.1 Create `src/application/use_cases/documents/__init__.py` (empty)
- [x] 5.2 Create `src/application/use_cases/documents/subir_documento.py` — `SubirDocumento.execute(SubirDocumentoInput)` with SHA-256 dedup check, storage persist, metadata + entity link
- [x] 5.3 Create `src/application/use_cases/documents/obtener_documentos.py` — `ObtenerDocumentos.by_entity(entity_type, entity_id)`
- [x] 5.4 Create `src/application/use_cases/documents/descargar_documento.py` — `DescargarDocumento.execute(document_id)` returning file bytes + metadata

## Phase 6: UI

- [x] 6.1 Create `src/ui/components/document_upload.py` — reusable NiceGUI `ui.upload` component accepting `entity_type` + `entity_id`, with progress/feedback
- [x] 6.2 Create `src/ui/pages/documentos.py` — gallery page at `/documentos` with AppShell, filtering, file table, download button
- [x] 6.3 Create file-serving handler at `/api/documents/{id}/file` via `@ui.page` with auth guard, returns `media_type` + `Content-Disposition`

## Phase 7: Container / Wiring

- [x] 7.1 Wire `FilesystemStorageService`, `SqlAlchemyDocumentRepository`, use cases in `src/infrastructure/container.py` — add factory methods, properties, and `__init__` wiring
- [x] 7.2 Add "Documentos" nav link (icon `description`) to `src/ui/components/shell.py`
- [x] 7.3 Register document gallery page in `main.py`

## Phase 8: Tests

- [x] 8.1 Test `FilesystemStorageService` — store/retrieve/delete/exists, dedup (no second write), missing file → raises FileNotFoundError, path nesting, base path config
- [x] 8.2 Test `InMemoryDocumentRepository` — full BaseRepo contract + DocumentRepoPort methods (get_by_claim_id, etc.)
- [x] 8.3 Test `SubirDocumento` — valid upload, dedup (same content → same hash), entity linkage, uploaded_by, description
