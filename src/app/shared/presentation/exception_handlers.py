"""
Global exception handlers for FastAPI application.

Provides consistent error response formats across all endpoints
for validation errors, domain errors, authentication errors, and unexpected exceptions.
"""

import os
import traceback

import sentry_sdk
from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from src.app.features.auth.domain.exceptions.auth_exceptions import AccountLockedError
from src.app.features.user.domain.exceptions.user_exceptions import UserAlreadyExistsError, UserNotFoundError
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
        content={"detail": message},
    )


async def value_error_handler(request: Request, exc: ValueError) -> JSONResponse:
    """
    Handle ValueError exceptions.

    Returns 400 with error message.

    Args:
        request: The incoming request
        exc: The value error exception

    Returns:
        JSONResponse with 400 status and error message
    """
    log.warning(f"Value error: {exc!s}")
    return JSONResponse(
        status_code=400,
        content={"detail": str(exc)},
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
        content={"detail": exc.message},
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
        content={"detail": exc.message},
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
        content={"detail": exc.message},
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
        content={"detail": exc.message},
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
        content={"detail": exc.message},
    )


async def user_not_found_error_handler(request: Request, exc: UserNotFoundError) -> JSONResponse:
    """
    Handle UserNotFoundError.

    Returns 404 with user not found message.

    Args:
        request: The incoming request
        exc: The user not found exception

    Returns:
        JSONResponse with 404 status and error message
    """
    log.warning(f"User not found: {exc}")
    return JSONResponse(
        status_code=404,
        content={"detail": str(exc)},
    )


async def user_already_exists_error_handler(request: Request, exc: UserAlreadyExistsError) -> JSONResponse:
    """
    Handle UserAlreadyExistsError.

    Returns 409 with conflict message.

    Args:
        request: The incoming request
        exc: The user already exists exception

    Returns:
        JSONResponse with 409 status and conflict message
    """
    log.warning(f"User already exists: {exc}")
    return JSONResponse(
        status_code=409,
        content={"detail": str(exc)},
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

    # This handler intercepts the exception before it reaches the ASGI layer,
    # so Sentry's automatic instrumentation never sees it — capture explicitly.
    # No-op if sentry_sdk.init() was never called (no SENTRY_DSN configured).
    sentry_sdk.capture_exception(exc)

    # In production, don't expose internal error details
    if ENV in ("prod", "production"):
        return JSONResponse(
            status_code=500,
            content={"detail": "An unexpected error occurred. Please try again later."},
        )
    # In dev/local, provide more details for debugging
    return JSONResponse(
        status_code=500,
        content={"detail": str(exc)},
    )


def register_exception_handlers(app):
    """
    Register all exception handlers with the FastAPI application.

    Args:
        app: FastAPI application instance
    """
    from slowapi import _rate_limit_exceeded_handler
    from slowapi.errors import RateLimitExceeded

    app.add_exception_handler(RequestValidationError, request_validation_error_handler)
    app.add_exception_handler(ValueError, value_error_handler)
    app.add_exception_handler(NotFoundError, not_found_error_handler)
    app.add_exception_handler(ValidationError, validation_error_handler)
    app.add_exception_handler(ConflictError, conflict_error_handler)
    app.add_exception_handler(AccountLockedError, account_locked_error_handler)
    app.add_exception_handler(DomainError, domain_error_handler)
    app.add_exception_handler(Exception, generic_exception_handler)
    app.add_exception_handler(UserNotFoundError, user_not_found_error_handler)
    app.add_exception_handler(UserAlreadyExistsError, user_already_exists_error_handler)
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
