"""Request logging middleware.

Logs every HTTP request with method, path, status, and latency.
Request ID and user ID are managed by RequestContextMiddleware
(ASGI-level) and are already in the logging context when this runs.
"""

import time
from collections.abc import Callable

import sentry_sdk
from fastapi import Request, Response

from src.app.shared.logging import get_logger, set_user_id


log = get_logger(__name__)

# The Client Review route carries its only credential (the project access code) in the path,
# so logging the raw path would write a live credential next to the client's IP.
_CREDENTIAL_PATH_PREFIX = "/v1/viewer/"
_CREDENTIAL_PATH_PLACEHOLDER = "/v1/viewer/{access_code}"


def loggable_path(path: str) -> str:
    """The request path with any credential segment replaced by its route template."""
    if path.startswith(_CREDENTIAL_PATH_PREFIX):
        return _CREDENTIAL_PATH_PLACEHOLDER
    return path


async def request_logging_middleware(request: Request, call_next: Callable) -> Response:
    """Log all HTTP requests with method, path, status, and latency.

    Request ID is already set in the logging context by
    RequestContextMiddleware. This function extracts user_id from
    request state (if auth dependency set it) for the summary line.
    """
    start_time = time.time()

    # Process request
    response = await call_next(request)

    # Calculate latency
    latency_ms = (time.time() - start_time) * 1000

    # Extract user_id from request state if authentication middleware set it
    user_id = getattr(request.state, "user_id", None)
    if user_id:
        set_user_id(str(user_id))
        # Internal ID only (never email/name) — send_default_pii=False in app.py
        # keeps Sentry from auto-capturing anything more identifying.
        sentry_sdk.set_user({"id": str(user_id)})

    # Log request summary — request_id is in context from RequestContextMiddleware
    log.info(
        "HTTP request processed",
        extra={
            "method": request.method,
            "path": loggable_path(request.url.path),
            "status_code": response.status_code,
            "latency_ms": round(latency_ms, 2),
            "client_host": request.client.host if request.client else None,
        },
    )

    return response
