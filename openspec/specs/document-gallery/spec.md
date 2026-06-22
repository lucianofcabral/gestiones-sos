# Document Gallery Specification

## Purpose

List and retrieve documents associated with an entity (claim, payment, invoice, etc.). The gallery displays document metadata and provides authenticated download/view access via hash-based URLs.

## Requirements

### Requirement: List Documents by Entity

The system MUST return all documents linked to a given entity through the `document_entities` table, ordered by `created_at` descending.

#### Scenario: Entity with documents

- GIVEN entity `c1` has 3 linked documents
- WHEN a user requests documents for `c1`
- THEN the system returns all 3 documents ordered by newest first

#### Scenario: Entity with no documents

- GIVEN entity `c1` has no linked documents
- WHEN a user requests documents for `c1`
- THEN the system returns an empty list

### Requirement: Gallery Display

The gallery component MUST show document name, type (icon/badge), size (human-readable), upload date, description, and a download/view action for each document.

#### Scenario: Gallery renders document list

- GIVEN entity `c1` has 2 documents
- WHEN the gallery component loads
- THEN each document card shows: filename, type badge, size, date, description, and download button

### Requirement: Document View/Download

The system MUST serve stored files via an authenticated endpoint at `/api/documents/{document_id}/file`. The response MUST include the original filename as `Content-Disposition` and the correct `Content-Type` MIME header.

#### Scenario: Authorized download

- GIVEN a document with MIME `application/pdf` and name `report.pdf`
- WHEN an authenticated user requests `/api/documents/{id}/file`
- THEN the system returns the file with `Content-Type: application/pdf` and `Content-Disposition: attachment; filename="report.pdf"`

#### Scenario: File not found on disk

- GIVEN a document row exists but the file is missing from the storage path
- WHEN a user requests the file
- THEN the system returns a 404 error

#### Scenario: Unauthenticated request

- GIVEN no authenticated user
- WHEN a request is made to `/api/documents/{id}/file`
- THEN the system returns a 401 error

### Requirement: Document Metadata Endpoint

The system MUST provide an endpoint `/api/documents/{document_id}` returning the document metadata (hash, name, size, mime, description, uploaded_by, created_at). Entity links MUST NOT be exposed through this endpoint.

#### Scenario: Fetch document metadata

- GIVEN a document with known ID
- WHEN an authenticated user requests `/api/documents/{id}`
- THEN the response includes hash, name, size, mime, description, uploaded_by, created_at
- AND entity links are not included

### Requirement: Error Handling for Missing Documents

If a document ID does not exist in the database, the system MUST return 404.

#### Scenario: Non-existent document

- GIVEN a document ID that does not exist
- WHEN a user requests metadata or file
- THEN the system returns a 404 error
