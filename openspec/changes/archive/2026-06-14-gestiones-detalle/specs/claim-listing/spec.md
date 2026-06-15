# Delta for Claim-Listing

## ADDED Requirements

### Requirement: Navigate to Claim Detail

Each row in the `/gestiones` table SHALL be clickable. When clicked, the system SHALL navigate to `/gestiones/{claim_id}` to display the full claim detail page. The click target SHALL be the entire row — not just a specific button or cell.

#### Scenario: Row click navigates to detail

- GIVEN the agent is viewing the gestiones list at `/gestiones`
- WHEN the agent clicks any row in the table
- THEN the system SHALL navigate to `/gestiones/{claim_id}` for that row's claim

#### Scenario: Navigation preserves back context

- GIVEN the agent navigates from `/gestiones` to `/gestiones/{claim_id}`
- WHEN the agent clicks the back link on the detail page
- THEN the system SHALL return to `/gestiones` with the same active/inactive filter state
