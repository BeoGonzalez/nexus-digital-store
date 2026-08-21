class DomainException(Exception):
    """Base exception for all domain logic."""


class ResourceNotFoundException(DomainException):
    """Raised when a requested resource is not found (maps to 404)."""


class BusinessRuleViolationException(DomainException):
    """Raised when a business rule is violated (maps to 409)."""


class UnauthorizedException(DomainException):
    """Raised for authentication or authorization failures (maps to 401)."""
