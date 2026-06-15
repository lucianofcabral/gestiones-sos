# Delta for Claim-Listing

## ADDED Requirements

### Requirement: Post-Registration Redirect

The system SHALL navigate to `/gestiones` after a successful registration from `/gestiones/nueva`. The redirected page SHALL display the newly created claim in the table. A positive notification SHALL confirm the result.

#### Scenario: New claim visible after registration redirect

- GIVEN the agent successfully registers a new claim
- WHEN the system redirects to `/gestiones`
- THEN the table SHALL include the newly created claim
- AND a positive `ui.notify` SHALL confirm the registration
