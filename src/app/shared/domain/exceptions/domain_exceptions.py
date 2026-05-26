"""
Shared domain exceptions.

Base exceptions used across all features to standardize error handling.
"""


class DomainError(Exception):
    """
    Base exception for domain logic errors.

    Raised when business rules are violated or domain invariants are broken.
    """

    def __init__(self, message: str = "Domain error occurred"):
        self.message = message
        super().__init__(self.message)


class NotFoundError(DomainError):
    """
    Raised when a requested resource is not found.

    Maps to HTTP 404 responses.
    """

    def __init__(self, resource: str, identifier: str):
        self.resource = resource
        self.identifier = identifier
        self.message = f"{resource} with ID '{identifier}' not found"
        super().__init__(self.message)


class ValidationError(DomainError):
    """
    Raised when input validation fails.

    Maps to HTTP 400 responses.
    """

    def __init__(self, message: str = "Validation failed"):
        super().__init__(message)


class ConflictError(DomainError):
    """
    Raised when a resource conflict occurs (e.g., duplicate).

    Maps to HTTP 409 responses.
    """

    def __init__(self, message: str = "Resource conflict"):
        super().__init__(message)
