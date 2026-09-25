"""
Global exception handlers for FastAPI application.

Provides consistent error response formats across all endpoints
for validation errors, domain errors, authentication errors, and unexpected exceptions.
"""

import os
import traceback
from typing import Any

import sentry_sdk
from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from src.app.features.ai_config.domain.exceptions.ai_config_exceptions import (
    ApiKeyNotFoundError,
    ApiKeyRejectedError,
    KeyValidationRateLimitedError,
)
from src.app.features.auth.domain.exceptions.auth_exceptions import AccountLockedError
from src.app.features.refinement.domain.exceptions.refinement_exceptions import RefinementFailedError
from src.app.features.user.domain.exceptions.user_exceptions import (
    AICreditsExhaustedError,
    UserAlreadyExistsError,
    UserNotFoundError,
)
from src.app.shared.domain.exceptions.domain_exceptions import (
    ConflictError,
    DomainError,
    NotFoundError,
    ValidationError,
)
from src.app.shared.infrastructure.security.api_key_cipher import ApiKeyDecryptionError
from src.app.shared.logging import get_logger


log = get_logger(__name__)


ENV = os.getenv("APP_ENV", "local")


def _redact_errors(errors: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Keep only the non-sensitive parts of a Pydantic error list.

    `exc.errors()` carries an `input` field holding the value that failed validation, and
    `ctx` can echo it too. For a rejected password or provider API key that is the secret
    itself, and the JSON log formatter copies every `extra` through verbatim — so it would
    reach CloudWatch and, via Sentry's logging breadcrumbs, Sentry (F-010 NFR-010-02).
    Which field failed and why is all a log needs.
    """
    return [{"type": error.get("type"), "loc": error.get("loc"), "msg": error.get("msg")} for error in errors]


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

    log.warning(f"Request validation error: {message}", extra={"validation_errors": _redact_errors(errors)})
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


async def ai_credits_exhausted_error_handler(request: Request, exc: AICreditsExhaustedError) -> JSONResponse:
    """
    Handle AICreditsExhaustedError exceptions.

    Returns 402, which the API contract reserves exclusively for a platform refinement
    attempted with no free credits left. The frontend keys the "add an API key" prompt off
    this status, so it must not be folded into the generic DomainError 422.

    Args:
        request: The incoming request
        exc: The credits exhausted exception

    Returns:
        JSONResponse with 402 status and the add-a-key prompt
    """
    log.info("AI credits exhausted", extra={"event_type": "ai_config.credits.exhausted"})
    return JSONResponse(
        status_code=402,
        content={"detail": str(exc), "code": "INSUFFICIENT_CREDITS"},
    )


async def api_key_rejected_error_handler(request: Request, exc: ApiKeyRejectedError) -> JSONResponse:
    """
    Handle ApiKeyRejectedError exceptions.

    Returns 422 with the provider, the failure reason, and whether the user should be sent
    to Settings to replace the key (FR-010-10/FR-010-11). The response carries no key
    material: `exc` is built from a classification, never from provider error text.

    Args:
        request: The incoming request
        exc: The provider rejection exception

    Returns:
        JSONResponse with 422 status and actionable guidance
    """
    log.warning(
        "Provider rejected an API key",
        extra={
            "event_type": "ai_config.key.rejected",
            "provider": exc.provider.value,
            "reason": exc.reason.value,
        },
    )
    return JSONResponse(
        status_code=422,
        content={
            "detail": str(exc),
            "code": "API_KEY_INVALID",
            "provider": exc.provider.value,
            "reason": exc.reason.value,
            "promptsKeyUpdate": exc.reason.prompts_key_update,
        },
    )


async def key_validation_rate_limited_error_handler(
    request: Request, exc: KeyValidationRateLimitedError
) -> JSONResponse:
    """
    Handle KeyValidationRateLimitedError exceptions.

    Returns 429 with Retry-After, matching how account lockout reports its cooldown.

    Args:
        request: The incoming request
        exc: The validation rate limit exception

    Returns:
        JSONResponse with 429 status and a Retry-After header
    """
    log.warning(
        "API key validation budget exhausted",
        extra={
            "event_type": "ai_config.key.validation_rate_limited",
            "retry_after_seconds": exc.retry_after_seconds,
        },
    )
    return JSONResponse(
        status_code=429,
        content={"detail": str(exc)},
        headers={"Retry-After": str(exc.retry_after_seconds)},
    )


async def api_key_not_found_error_handler(request: Request, exc: ApiKeyNotFoundError) -> JSONResponse:
    """
    Handle ApiKeyNotFoundError exceptions.

    Returns 404 when an operation targets a provider the user holds no key for.

    Args:
        request: The incoming request
        exc: The missing key exception

    Returns:
        JSONResponse with 404 status
    """
    return JSONResponse(
        status_code=404,
        content={"detail": str(exc), "provider": exc.provider.value},
    )


async def api_key_decryption_error_handler(request: Request, exc: ApiKeyDecryptionError) -> JSONResponse:
    """
    Handle ApiKeyDecryptionError exceptions.

    A stored key that will not decrypt means the master key moved or the row was tampered
    with. Left to the generic handler this became an opaque 500 plus a Sentry issue on
    every refinement, with nothing telling the user how to recover. It is reported as a
    422 in the same shape as a provider rejection, so the frontend's existing
    "update your key" path handles it.

    Args:
        request: The incoming request
        exc: The decryption failure

    Returns:
        JSONResponse with 422 status and re-entry guidance
    """
    log.error(
        "A stored API key could not be decrypted",
        extra={"event_type": "ai_config.key.undecryptable"},
    )
    return JSONResponse(
        status_code=422,
        content={
            "detail": "This stored API key can no longer be read. Delete it and add the key again.",
            "code": "API_KEY_INVALID",
            "promptsKeyUpdate": True,
        },
    )


async def refinement_failed_error_handler(request: Request, exc: RefinementFailedError) -> JSONResponse:
    """
    Handle RefinementFailedError exceptions.

    Returns 502 with the Admin's raw notes echoed back, so a provider outage costs no
    re-entry: the client can resubmit the preserved input as-is (FR-002-04).

    Args:
        request: The incoming request
        exc: The refinement failure exception

    Returns:
        JSONResponse with 502 status, actionable guidance, and the preserved raw notes
    """
    log.warning(
        "Refinement failed",
        extra={
            "event_type": "refinement.failed",
            "provider": exc.provider,
            "failure_class": exc.failure_class.value,
        },
    )
    return JSONResponse(
        status_code=502,
        content={
            "detail": str(exc),
            "failureClass": exc.failure_class.value,
            "provider": exc.provider,
            "rawNotes": exc.raw_notes,
        },
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
    app.add_exception_handler(RefinementFailedError, refinement_failed_error_handler)
    app.add_exception_handler(AICreditsExhaustedError, ai_credits_exhausted_error_handler)
    app.add_exception_handler(ApiKeyRejectedError, api_key_rejected_error_handler)
    app.add_exception_handler(ApiKeyNotFoundError, api_key_not_found_error_handler)
    app.add_exception_handler(KeyValidationRateLimitedError, key_validation_rate_limited_error_handler)
    app.add_exception_handler(ApiKeyDecryptionError, api_key_decryption_error_handler)
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
