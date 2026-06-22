# Group Claim Specification

## Purpose

CRUD lifecycle for GroupClaim entities — create, list/search, update name, delete, and look up by associated claim ID or by group name. Groups allow multiple claims to enter together on the same invoice while staying individually registrable.

## Requirements

### Requirement: Create Group Claim

The system MUST create a GroupClaim with fields: `group_id` (UUID, auto-generated), `name` (string, 1–100 chars, unique), `created_at` (datetime, auto-generated).

When `name` already exists in the store, the system MUST NOT create a duplicate and MUST return the existing GroupClaim.

#### Scenario: Happy path — new group name
- GIVEN a group name that does not exist in the store
- WHEN the use case executes with that `name`
- THEN the system creates a GroupClaim with the given `name`, generates a `group_id` and `created_at`, and returns it

#### Scenario: Duplicate group name
- GIVEN a GroupClaim with name "Grupo A" already exists in the store
- WHEN the use case executes with `name="Grupo A"`
- THEN the system returns the existing GroupClaim without creating a new one

### Requirement: List All Group Claims

The system MUST return all GroupClaims ordered by `name` ascending.

#### Scenario: Multiple groups exist
- GIVEN several GroupClaims in the store
- WHEN the use case executes
- THEN the system returns the full list ordered by `name` ascending

#### Scenario: No groups exist
- GIVEN no GroupClaims in the store
- WHEN the use case executes
- THEN the system returns an empty list

### Requirement: Search Group Claims by Text

The system MUST return GroupClaims whose `name` contains the given text (case-insensitive, partial match — ILIKE semantics).

#### Scenario: Matching groups found
- GIVEN GroupClaims with names "Accidentes", "Robo Total", "Accidentes Menores"
- WHEN `get_by_text_like("accidente")` is called
- THEN the system returns ["Accidentes", "Accidentes Menores"]

#### Scenario: No matches
- GIVEN GroupClaims with names "Robo Total", "Incendio"
- WHEN `get_by_text_like("xx")` is called
- THEN the system returns an empty list

### Requirement: Get Group Claim by ID

The system MUST return a GroupClaim by `group_id`, or `None` if not found.

#### Scenario: Group exists
- GIVEN a GroupClaim exists in the store
- WHEN `get_by_id(group_id)` is called
- THEN the system returns the matching GroupClaim

#### Scenario: Group not found
- GIVEN no GroupClaim for the given `group_id`
- WHEN `get_by_id(group_id)` is called
- THEN the system returns `None`

### Requirement: Get Group Claim by Name

The system MUST return a GroupClaim by exact `name` match, or `None` if not found.

#### Scenario: Group exists by name
- GIVEN a GroupClaim with name "Accidentes" exists
- WHEN `get_by_group_name("Accidentes")` is called
- THEN the system returns the matching GroupClaim

#### Scenario: Group not found by name
- GIVEN no GroupClaim with the given name
- WHEN `get_by_group_name("Inexistente")` is called
- THEN the system returns `None`

### Requirement: Get Group Claim by Claim ID

The system MUST return the GroupClaim associated with a given `claim_id` via a JOIN on `claims.group_id`, or `None` if the claim has no associated group.

#### Scenario: Claim belongs to a group
- GIVEN a Claim with `claim_id` whose `group_id` references an existing GroupClaim
- WHEN `get_by_claim_id(claim_id)` is called
- THEN the system returns the associated GroupClaim

#### Scenario: Claim has no group
- GIVEN a Claim with `claim_id` whose `group_id` does not reference any GroupClaim
- WHEN `get_by_claim_id(claim_id)` is called
- THEN the system returns `None`

#### Scenario: Claim does not exist
- GIVEN no Claim for the given `claim_id`
- WHEN `get_by_claim_id(claim_id)` is called
- THEN the system returns `None`

### Requirement: Update Group Claim Name

The system MUST update the `name` field of a GroupClaim by `group_id`. Returns `True` on success, `False` if not found. The new name MUST still satisfy the unique constraint.

#### Scenario: Update existing group name
- GIVEN a GroupClaim with `group_id` and current name "Viejos"
- WHEN the use case executes with a new `name="Nuevos"`
- THEN the system updates the name and returns `True`

#### Scenario: Update non-existent group
- GIVEN no GroupClaim for the given `group_id`
- WHEN the use case executes
- THEN the system returns `False`

#### Scenario: Update to duplicate name
- GIVEN GroupClaims with names "Grupo A" and "Grupo B"
- WHEN the use case tries to rename "Grupo B" to "Grupo A"
- THEN the system raises a constraint violation or returns `False`

### Requirement: Delete Group Claim

The system MUST delete a GroupClaim by `group_id`. It MUST NOT delete if any Claim references this `group_id`, to preserve referential integrity.

#### Scenario: Delete group with no claims
- GIVEN a GroupClaim with no Claim referencing its `group_id`
- WHEN the use case executes
- THEN the system deletes the GroupClaim

#### Scenario: Delete non-existent group
- GIVEN no GroupClaim for the given `group_id`
- WHEN the use case executes
- THEN the system does nothing (no-op)

#### Scenario: Delete group with associated claims
- GIVEN a GroupClaim that has one or more Claims with its `group_id`
- WHEN the use case executes
- THEN the system raises `ValueError` (or equivalent) and does NOT delete
