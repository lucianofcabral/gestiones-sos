# Delta for Document Gallery (Documentos Table Refactoring)

## ADDED Requirements

### Requirement: Related Entities Table with ui.table Component

The documentos page MUST render a native `ui.table` component displaying documents grouped and enriched by their related entities (Claim, Invoice, Group). Table SHALL display columns: Documento (entity type/reference), Categoría (entity type badge), Fecha, Detalle (file count, preview). All entity lookups MUST be pre-computed before table render to avoid N+1 queries.

#### Scenario: Document table renders with entity enrichment

- GIVEN documents linked to various entities (claims, invoices, groups)
- WHEN documentos page loads
- THEN `ui.table` displays documents with pre-resolved entity data
- AND columns: Documento, Categoría, Fecha, Detalle
- AND uses semantic HTML structure (`<table>`, `<thead>`, `<tbody>`, `<tr>`, `<td>`)

#### Scenario: Documento column shows entity type and reference

- GIVEN documents linked to different entity types
- WHEN table renders
- THEN Documento column displays:
  - For claims: "Gestión" + claim reference (not "documento" text)
  - For invoices: "Factura" + invoice number (not "documento" text)
  - For groups: "Grupo" + group name (not "documento" text)
- AND text per _ENTITY_TYPE_LABELS mapping in current code

#### Scenario: Categoría column shows colored badge per entity type

- GIVEN documents linked to various entities
- WHEN Categoría column renders
- THEN displays Badge component with colors:
  - Claim entity → dark blue (#1a5276)
  - Invoice entity → dark green (#1e8449)
  - Group entity → dark purple (#7d3c98)
- AND styling: `text-xs font-bold px-2 py-0.5 rounded-full {bg-color} text-white`
- AND text shows entity type ("Gestión", "Factura", "Grupo")

#### Scenario: All entity lookups pre-computed

- GIVEN documents table about to render
- WHEN data loading phase completes
- THEN all Claim, Invoice, and Group lookups completed once before render
- AND no N+1 queries during table render

### Requirement: Document Pagination and Filtering

The documentos table MUST support pagination with 12 items per page and filtering by: entity_type, date_from, date_to, text search (entity name/reference). Sorting MUST work on all columns; filtering resets pagination to page 1.

#### Scenario: Pagination shows 12 documents per page

- GIVEN 100+ documents linked to various entities
- WHEN documentos table renders
- THEN pagination UI shows 12 items per page
- AND "< Anterior" and "Siguiente >" buttons functional

#### Scenario: Filter by entity type

- GIVEN documents linked to claims, invoices, and groups
- WHEN user filters by entity_type="Gestión"
- THEN table shows only documents linked to claims
- AND pagination resets to page 1

#### Scenario: Filter by date range

- GIVEN documents with varying dates
- WHEN user enters date_from and date_to and applies
- THEN table shows only documents within range
- AND sorting works within filtered set

#### Scenario: Text search across entity references

- GIVEN documents linked to entities with various names/references
- WHEN user enters search text
- THEN table searches across entity names and references
- AND displays matching documents

#### Scenario: Sort on all columns

- GIVEN documentos table
- WHEN user clicks any column header (Documento, Categoría, Fecha, Detalle)
- THEN table sorts by that column
- AND clicking again reverses sort direction
- AND sort direction indicator shown in header

### Requirement: Document Row Click Behavior

Each row in the documentos table, when clicked, MAY open the detail/edit dialog for the related entity (Claim, Invoice, Group) depending on entity type. Row click interaction MUST NOT interfere with document selection or other operations. If entity detail dialog is not applicable, row click has no effect.

#### Scenario: Row click opens claim detail dialog

- GIVEN a document row linked to a claim entity
- WHEN user clicks anywhere on the row
- THEN the system MAY open the claim detail dialog for that claim
- OR no action occurs (depends on current UX design)

#### Scenario: Row click opens invoice dialog

- GIVEN a document row linked to an invoice entity
- WHEN user clicks anywhere on the row
- THEN the system MAY open the invoice detail dialog
- OR no action occurs

#### Scenario: Row click opens group dialog

- GIVEN a document row linked to a group entity
- WHEN user clicks anywhere on the row
- THEN the system MAY open the group detail dialog
- OR no action occurs

### Requirement: Document Action Icons

Each row in the documentos table MUST display action icons in the Acciones column (if applicable): View (eye icon), Download (download icon), Delete (trash icon).

Behavior:

- **View**: opens document/file in browser or downloads based on mime type
- **Download**: forces file download
- **Delete**: opens confirmation dialog and deletes document (if no references block deletion)

#### Scenario: View icon opens document preview

- GIVEN user clicks view icon on document row
- WHEN click executes
- THEN document file opened in browser (image, PDF) or download triggered
- AND behavior depends on file mime type

#### Scenario: Download icon forces file download

- GIVEN user clicks download icon
- WHEN click executes
- THEN file downloaded to user's downloads folder
- AND original filename preserved

#### Scenario: Delete icon deletes document

- GIVEN user clicks delete icon
- WHEN user confirms in dialog
- THEN document deleted from system
- AND table refreshes
- AND error shown if deletion blocked due to references

### Requirement: Entity Type Categorization

Document rows MUST display the correct entity type category (Gestión, Factura, Grupo) based on the document's `entity_type` field. Each entity type MUST map to a color and label per _ENTITY_TYPE_LABELS and color scheme in current code.

#### Scenario: Entity type mapping

- GIVEN documents with various entity_type values
- WHEN Categoría column renders
- THEN mapping applies:
  - `entity_type=CLAIM` → Badge("Gestión", color=blue)
  - `entity_type=INVOICE` → Badge("Factura", color=green)
  - `entity_type=GROUP_CLAIM` → Badge("Grupo", color=purple)

#### Scenario: Badge color consistency

- GIVEN multiple documents of same entity type
- WHEN Categoría column renders
- THEN all badges for that type display with identical color
- AND styling matches current page badge colors exactly

### Requirement: Date Column Display

The Fecha column MUST display the document's creation date in a consistent, readable format. Format MUST match current page display (e.g., "DD/MM/YYYY" or locale-appropriate format).

#### Scenario: Date displays in consistent format

- GIVEN documents with varying creation dates
- WHEN Fecha column renders
- THEN all dates display in consistent format
- AND format matches current page display exactly
- AND dates properly sorted when user clicks Fecha header

---

## REMOVED Requirements

### Requirement: Manual Row Display via ui.row()

The previous manual `ui.row()` layout for displaying documents is removed. All documents now rendered via native `ui.table` component with semantic HTML.

(Reason: Conversion to ui.table component per refactoring plan)

---

## Implementation Notes

- All entity lookups (Claim, Invoice, Group) pre-computed once before table render to avoid N+1 queries
- Categoría badges use Badge helper from ui-table-components spec
- Entity type mapping and colors defined in _ENTITY_TYPE_LABELS and color constants in documentos.py
- Sort and filter behavior identical to current page
- Row click behavior optional; may be implemented or left as no-op pending UX design confirmation
- Action icons (view, download, delete) match current page behavior
- Pagination independent between document list and any nested/detail views
