# Delta for document-gallery

## Overview

The `/documentos` page gains a view toggle, category-based document grouping, document selection with a related-entities detail table, and one-click entity navigation. Existing List View and download behavior is preserved.

## ADDED Requirements

### Requirement: View Toggle

The page MUST provide a toggle between "Lista" (default) and "Categorías" views. Switching views MUST NOT trigger a page reload.

#### Scenario: Switch to category view

- GIVEN the page is in List View
- WHEN the user clicks "Categorías"
- THEN the view switches to Category View with expandable sections

#### Scenario: Switch back to list view

- GIVEN the page is in Category View
- WHEN the user clicks "Lista"
- THEN the view switches back to the flat table

### Requirement: Category View

The Category View MUST group documents into three expandable sections: "Gestiones", "Facturas", "Grupos". A document MAY appear in multiple sections. Each section header MUST show the entity type name and the count of linked entities.

#### Scenario: Documents grouped by entity type

- GIVEN documents linked to invoices, claims, and groups
- WHEN the user switches to Category View
- THEN three sections render with documents grouped by entity type
- AND a document linked to multiple entity types appears in each relevant section

#### Scenario: Empty category section

- GIVEN no document links to any "Facturas" entity
- WHEN the user switches to Category View
- THEN the "Facturas" section shows an empty state message

### Requirement: Document Selection

The system MUST track a selected document via reactive state. Clicking a document row in either view MUST set the selection and populate the related-entities table.

#### Scenario: Select document from list view

- GIVEN the user is in List View
- WHEN the user clicks a document row
- THEN that document is selected
- AND the related-entities table shows its linked entities

#### Scenario: Deselect document

- GIVEN a document is selected
- WHEN the user clicks the same document again
- THEN the document is deselected
- AND the related-entities table clears

### Requirement: Related-Entities Table

A table at the page top MUST show entities linked to the selected document. The table MUST persist above both views. Each row MUST show: document name, entity category (colored badge), entity `created_at`, and category-specific info.

Category-specific columns:
- "Factura": invoice number, period
- "Gestión": claim tipo, número, patente, póliza, cliente
- "Grupo": group name, member count

#### Scenario: Related-entities populates on selection

- GIVEN a document linked to 1 invoice and 1 claim
- WHEN the user selects that document
- THEN the table shows 2 rows with correct category-specific data
- AND category badges use distinct colors per entity type

#### Scenario: Document with no entity links

- GIVEN a document with no entity links
- WHEN the user selects that document
- THEN the table shows an empty state

### Requirement: Entity Navigation

Clicking a row in the related-entities table MUST open the existing dialog or detail page for that entity.

#### Scenario: Navigate to invoice dialog

- GIVEN a row for entity type "Factura"
- WHEN the user clicks that row
- THEN the existing invoice edit dialog opens

#### Scenario: Navigate to group dialog

- GIVEN a row for entity type "Grupo"
- WHEN the user clicks that row
- THEN the existing group edit dialog opens

#### Scenario: Navigate to claim detail

- GIVEN a row for entity type "Gestión"
- WHEN the user clicks that row
- THEN the user is navigated to `/gestiones/{id}`

### Requirement: Document Entities Repository Method

The `DocumentRepoPort` protocol MUST include `get_document_entities(document_id: UUID) -> list[dict]` returning entity links from the `document_entities` table.

#### Scenario: Repository returns entity links

- GIVEN a document has 2 entity links
- WHEN `get_document_entities` is called
- THEN it returns a list of dicts with document_id, entity_type, entity_id, and created_at

#### Scenario: Document with no entities

- GIVEN a document has no entity links
- WHEN `get_document_entities` is called
- THEN it returns an empty list

## Affected Files

| File | Change |
|------|--------|
| `src/ui/pages/documentos.py` | Add toggle, category view, selection state, related-entities table, entity navigation |
| `src/domain/ports/repositories.py` | Add `get_document_entities` to `DocumentRepoPort` |
