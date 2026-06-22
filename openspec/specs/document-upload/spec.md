# Document Upload Specification

## Purpose

Upload documents (PDF, JPG, PNG) associated with polymorphic entities via content-addressable filesystem storage. SHA-256 hash provides automatic dedup. Metadata is persisted in the `documents` and `document_entities` tables.

## Requirements

### Requirement: Accepted File Types

The system MUST accept PDF, JPG, and PNG files. The system MUST validate file type by both extension and MIME. The system MUST reject unsupported types with a 400 error.

#### Scenario: Upload valid PDF

- GIVEN a user selects a `.pdf` file with MIME `application/pdf`
- WHEN they submit the upload form
- THEN the file is accepted and processed

#### Scenario: Reject unsupported file type

- GIVEN a user selects a `.exe` file with MIME `application/x-msdownload`
- WHEN they submit the upload form
- THEN the system returns a 400 error with message "Unsupported file type"

### Requirement: File Size Limit

The system MUST enforce a maximum file size of 16 MB. Larger files MUST be rejected with a 413 error before storage.

#### Scenario: File within limit

- GIVEN a user selects a 10 MB file
- WHEN they submit the upload
- THEN the file is accepted

#### Scenario: File exceeds limit

- GIVEN a user selects a 20 MB file
- WHEN they submit the upload
- THEN the system returns a 413 error with message "File exceeds maximum size of 16 MB"

### Requirement: Content-Addressable Dedup

The system MUST compute the SHA-256 hash of the file content before storage. If a document with the same hash already exists, the system MUST reuse the stored file and create only the entity-linkage record. The system MUST NOT store duplicate files on disk.

#### Scenario: New file upload

- GIVEN no document exists with the given file's SHA-256 hash
- WHEN the upload completes
- THEN the file is written to `{hash[:2]}/{hash[2:4]}/{hash}.{ext}` and a new `document` row is created

#### Scenario: Duplicate file upload

- GIVEN a document with hash `abc123...` already exists on disk
- WHEN a user uploads a file with the same hash
- THEN no new file is written to disk and only a new `document_entities` link is created

### Requirement: Entity Linkage

The upload form MUST accept an `entity_type` and `entity_id` parameter. The system MUST create a `document_entities` row linking the document to the specified entity.

#### Scenario: Upload linked to a claim

- GIVEN a user uploads a PDF for claim UUID `c1`
- WHEN the upload completes
- THEN a `document_entities` row exists with `entity_type=claim` and `entity_id=c1`

#### Scenario: Upload without entity link

- GIVEN a user uploads without specifying an entity
- WHEN the upload completes
- THEN the document is stored standalone with no `document_entities` row

### Requirement: Metadata Persistence

The system MUST persist `document_hash`, `type` (original extension), `name` (original filename), `size` (bytes), `mime`, `description`, and `uploaded_by` in the `documents` table upon successful upload.

#### Scenario: Metadata stored correctly

- GIVEN a user uploads `report.pdf`
- WHEN the upload completes
- THEN the `documents` table contains a row with the correct hash, name, size, MIME type, description, and uploader

### Requirement: Description and Uploaded By

The upload form SHOULD accept optional `description` and MUST capture `uploaded_by` (current user ID). If `uploaded_by` is not provided, the system MUST reject the upload.

#### Scenario: Upload with authenticated user

- GIVEN an authenticated user with ID `u1`
- WHEN they upload a file
- THEN `uploaded_by` is set to `u1`

#### Scenario: Upload without user context

- GIVEN a request with no authenticated user
- WHEN the upload is attempted
- THEN the system returns a 401 error
