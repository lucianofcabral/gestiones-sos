"""Typed domain exceptions for the gestiones-sos application.

All business-rule violations raise one of these typed exceptions
instead of bare ``ValueError``.  This gives callers and middleware
a clear type-level API for error handling.

The base class inherits from ``ValueError`` so that existing
``except ValueError`` catch blocks (e.g. in UI routes) continue
to work during the migration period.
"""


class DomainError(ValueError):
    """Base exception for all domain-rule violations."""


class ClaimNotFoundError(DomainError):
    """The requested claim does not exist."""


class ClaimHasActivePaymentsError(DomainError):
    """The claim has at least one active payment and cannot be deleted."""


class GestionAlreadyExistsError(DomainError):
    """A SOS gestion with the same number already exists."""


class PeriodRequiredError(DomainError):
    """A period ID is required for NC payments."""


class AgentNotConfiguredError(DomainError):
    """The SOS or SM agent has not been configured in the system."""


class InvalidNCConfigurationError(DomainError):
    """The NC payment configuration (payer/payee) is invalid."""


class InvalidPaymentUpdateError(DomainError):
    """The requested payment update violates editability rules."""


class InvalidCredentialsError(DomainError):
    """The provided email or password is incorrect."""


class UserInactiveError(DomainError):
    """The user account is inactive and cannot perform this action."""


class EmailAlreadyRegisteredError(DomainError):
    """A user with this email address already exists."""


class UserNotFoundError(DomainError):
    """The specified user does not exist."""


class InvalidTokenError(DomainError):
    """The provided token is invalid or has expired."""
