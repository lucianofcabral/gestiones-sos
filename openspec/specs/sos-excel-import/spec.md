# SOS Import Specification

## Purpose

Upload an Excel file exported from the external SOS system ("Gestión Reclamos y Reintegros" format), parse each row, and upsert (create or update) a Claim + SosClaim per row. Each row processes in its own transaction.

## Requirements

### Requirement: Upload Page & Preview

The system MUST serve a page at `/gestiones/importar` with a file picker (`ui.upload`), a preview table of parsed rows, and an "Import" button.

| Scenario | GIVEN | WHEN | THEN |
|---|---|---|---|
| Page renders | User navigates to `/gestiones/importar` | Page loads | User sees file picker, empty preview, Import button |
| Preview parsed rows | User picks a valid `.xlsx` with 3 data rows | System parses the file | Preview table shows the 3 parsed rows |
| Reject non-xlsx | User uploads a `.csv` file | System reads the upload | Shows "Formato no soportado. Seleccione un archivo .xlsx" |

### Requirement: Excel Parsing

The system MUST parse `.xlsx` files. It MUST skip the "N° Caso" column and map the following columns:

| Excel Column | Domain Field |
|---|---|
| `N° Gestión` | `gestion` |
| `Fecha` | `created_at` (on Claim) |
| `Asegurado` | `claimer_name` |
| `Póliza` | `policy_number` |
| `Patente` | `plate` |
| `Categoría` | `category` (on SosClaim) |
| `Motivo` | `reason` (on SosClaim) |
| `Estado` | `status` (on SosClaim) |
| `Carga` | `load_user` (on SosClaim) |
| `Responde` | `response_user` (on SosClaim) |
| `ITR` | `itr` (on SosClaim) |

| Scenario | GIVEN | WHEN | THEN |
|---|---|---|---|
| Missing `N° Gestión` | Excel file lacks that column | Parser reads the file | Error returned, no preview shown |
| Wrong sheet name | `.xlsx` sheet name does not match expected | Parser opens the file | Error returned with sheet name expected |

### Requirement: Upsert Logic (Per-Row Transaction)

Each row MUST be processed in its own UoW transaction. For each row, the system MUST:

1. Look up `SosClaim` by `gestion` via `SosClaimRepoPort.get_by_number`
2. **If found**: update the existing SosClaim fields AND its linked Claim fields
3. **If not found**: create a new Claim (with `claimed_amount=0.01`) AND a new SosClaim

| Scenario | GIVEN | WHEN | THEN |
|---|---|---|---|
| Create new | Row `gestion=12345` does not exist in store | Row processed | Claim created with `claimed_amount=0.01`, SosClaim created with `gestion=12345` |
| Update existing | SosClaim `gestion=12345` linked to Claim C exists | Row with different `status` processed | Claim C fields and SosClaim updated; no new entities created |
| Duplicate gestion in file | Two rows share `gestion=12345` | First row creates, second row finds existing | Second row updates the existing entities (no error) |

### Requirement: Claim Kind Resolution

At import start, the system MUST resolve `claim_kind_id` via `ClaimKindRepoPort.get_by_name("SOS")`.

| Scenario | GIVEN | WHEN | THEN |
|---|---|---|---|
| Found | ClaimKind with name "SOS" exists | Import begins | `claim_kind_id` resolved, import proceeds |
| Not found | No ClaimKind named "SOS" | Import begins | Import aborts with clear error, no rows processed |

### Requirement: Group Resolution

At import start, the system MUST resolve a default `group_id` by fetching the first active GroupClaim.

| Scenario | GIVEN | WHEN | THEN |
|---|---|---|---|
| Active group exists | At least one GroupClaim exists | Import begins | Its `group_id` used for all rows |
| No groups | No GroupClaim exists | Import begins | Import aborts with clear error |

### Requirement: Per-Row Error Isolation

A failure on one row MUST NOT prevent others from processing. Errors MUST be collected per row.

| Scenario | GIVEN | WHEN | THEN |
|---|---|---|---|
| Partial failure | 3 rows, 2nd has non-integer `gestion` | Import executes | Rows 1 and 3 succeed, row 2 reported as error |
| Duplicate key race | Row's `gestion` inserted concurrently by another session | UoW commit fails | That row reported as error, others unaffected |

### Requirement: Results Summary

After all rows process, the system MUST display a summary with counts: created, updated, errors.

| Scenario | GIVEN | WHEN | THEN |
|---|---|---|---|
| Mixed results | 5 rows: 2 create, 2 update, 1 error | Import finishes | Summary shows "Creados: 2, Actualizados: 2, Errores: 1" |
| All success | 3 rows all create | Import finishes | Summary shows "Creados: 3, Actualizados: 0, Errores: 0" |
| All fail | 2 rows both invalid | Import finishes | Summary shows "Creados: 0, Actualizados: 0, Errores: 2" |

## Non-Functional

- Files up to 10 MB MUST be accepted
- Preview MUST render within 2 s for files under 5 MB
- Each row transaction SHOULD complete within 5 s
- The import MUST NOT block the UI; the user SHOULD see a progress indication
