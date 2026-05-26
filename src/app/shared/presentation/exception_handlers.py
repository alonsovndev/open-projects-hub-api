"""
Global exception handlers for FastAPI application.

Provides consistent error response formats across all endpoints
for validation errors, domain errors, authentication errors, and unexpected exceptions.
"""

import os
import traceback

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from src.app.features.auth.domain.exceptions.auth_exceptions import AccountLockedError
from src.app.shared.domain.exceptions.domain_exceptions import (
    ConflictError,
    DomainError,
    NotFoundError,
    ValidationError,
)
from src.app.shared.logging import get_logger


log = get_logger(__name__)


ENV = os.getenv("APP_ENV", "local")


async def request_validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """
    Handle FastAPI/Pydantic RequestValidationError exceptions.

    Returns 422 with consistent error envelope matching domain validation errors.

    Args:
        request: The incoming request
        exc: The validation error exception

    Returns:
        JSONResponse with 422 status and error details
    """
    # Extract first error message for simplicity (can be enhanced to show all errors)
    errors = exc.errors()
    first_error = errors[0] if errors else {}
    field = " -> ".join(str(loc) for loc in first_error.get("loc", []))
    error_msg = first_error.get("msg", "Invalid request data")

    # Build user-friendly message
    message = f"Validation failed for field '{field}': {error_msg}" if field else error_msg

    log.warning(f"Request validation error: {message}", extra={"validation_errors": errors})
    return JSONResponse(
        status_code=422,
        content={
            "error": "Validation Error",
            "message": message,
        },
    )


async def not_found_error_handler(request: Request, exc: NotFoundError) -> JSONResponse:
    """
    Handle NotFoundError exceptions.

    Returns 404 with resource information.

    Args:
        request: The incoming request
        exc: The not found error exception

    Returns:
        JSONResponse with 404 status and resource details
    """
    log.warning(f"Resource not found: {exc.message}")
    return JSONResponse(
        status_code=404,
        content={
            "error": "Not Found",
            "message": exc.message,
            "resource": exc.resource,
            "identifier": exc.identifier,
        },
    )


async def validation_error_handler(request: Request, exc: ValidationError) -> JSONResponse:
    """
    Handle ValidationError exceptions.

    Returns 400 with validation error details.

    Args:
        request: The incoming request
        exc: The validation error exception

    Returns:
        JSONResponse with 400 status and error message
    """
    log.warning(f"Validation error: {exc.message}")
    return JSONResponse(
        status_code=400,
        content={
            "error": "Validation Error",
            "message": exc.message,
        },
    )


async def conflict_error_handler(request: Request, exc: ConflictError) -> JSONResponse:
    """
    Handle ConflictError exceptions.

    Returns 409 with conflict details.

    Args:
        request: The incoming request
        exc: The conflict error exception

    Returns:
        JSONResponse with 409 status and conflict message
    """
    log.warning(f"Conflict error: {exc.message}")
    return JSONResponse(
        status_code=409,
        content={
            "error": "Conflict",
            "message": exc.message,
        },
    )


async def account_locked_error_handler(request: Request, exc: AccountLockedError) -> JSONResponse:
    """
    Handle AccountLockedError exceptions.

    Returns 429 (Too Many Requests) with lockout details.

    Args:
        request: The incoming request
        exc: The account locked error exception

    Returns:
        JSONResponse with 429 status and lockout information
    """
    log.warning(
        f"Account locked: {exc.message}",
        extra={"remaining_seconds": exc.remaining_seconds, "failed_attempts": exc.failed_attempts},
    )
    return JSONResponse(
        status_code=429,
        content={
            "error": "Account Locked",
            "message": exc.message,
            "remaining_seconds": exc.remaining_seconds,
            "failed_attempts": exc.failed_attempts,
        },
        headers={"Retry-After": str(exc.remaining_seconds)},
    )


async def domain_error_handler(request: Request, exc: DomainError) -> JSONResponse:
    """
    Handle generic DomainError exceptions.

    Returns 422 for business logic errors.

    Args:
        request: The incoming request
        exc: The domain error exception

    Returns:
        JSONResponse with 422 status and error message
    """
    log.error(f"Domain error: {exc.message}")
    return JSONResponse(
        status_code=422,
        content={
            "error": "Domain Error",
            "message": exc.message,
        },
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Handle all unhandled exceptions.

    Returns 500 with generic error message (no sensitive details in production).

    Args:
        request: The incoming request
        exc: The unhandled exception

    Returns:
        JSONResponse with 500 status and error details
    """
    log.error(f"Unhandled exception: {exc!s}")
    log.error(traceback.format_exc())

    # In production, don't expose internal error details
    if ENV in ("prod", "production"):
        return JSONResponse(
            status_code=500,
            content={
                "error": "Internal Server Error",
                "message": "An unexpected error occurred. Please try again later.",
            },
        )
    # In dev/local, provide more details for debugging
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "message": str(exc),
            "type": exc.__class__.__name__,
        },
    )


def register_exception_handlers(app):
    """
    Register all exception handlers with the FastAPI application.

    Args:
        app: FastAPI application instance
    """
    from fastapi.exceptions import RequestValidationError
    from slowapi import _rate_limit_exceeded_handler
    from slowapi.errors import RateLimitExceeded

    app.add_exception_handler(RequestValidationError, request_validation_error_handler)
    app.add_exception_handler(NotFoundError, not_found_error_handler)
    app.add_exception_handler(ValidationError, validation_error_handler)
    app.add_exception_handler(ConflictError, conflict_error_handler)
    app.add_exception_handler(AccountLockedError, account_locked_error_handler)
    app.add_exception_handler(DomainError, domain_error_handler)
    app.add_exception_handler(Exception, generic_exception_handler)
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
