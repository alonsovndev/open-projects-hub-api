"""
Request logging middleware with correlation ID and user identification support.

Logs every HTTP request with method, path, status, latency, correlation ID, and authenticated user.
"""

import time
from collections.abc import Callable

from fastapi import Request, Response

from src.app.shared.logging import get_logger, set_user_context
from src.app.shared.logging.correlation import correlation_id


log = get_logger(__name__)


async def request_logging_middleware(request: Request, call_next: Callable) -> Response:
    """
    Middleware to log all HTTP requests with correlation IDs and user identification.

    Reads the correlation ID from the contextvar set by CorrelationIdMiddleware
    (the app-level ASGI middleware).  Does NOT generate its own ID — that would
    create a discrepancy between the ID seen in application logs and the one
    reported in this middleware's summary line.

    Args:
        request: FastAPI request object
        call_next: Next middleware/handler in the chain

    Returns:
        Response from the downstream handler
    """
    request_id = correlation_id.get() or "N/A"

    # Record start time
    start_time = time.time()

    # Process request
    response = await call_next(request)

    # Calculate latency
    latency_ms = (time.time() - start_time) * 1000

    # Extract user_id from request state if authentication middleware set it
    user_id = getattr(request.state, "user_id", None) or "anonymous"

    # Set user context for correlation
    set_user_context(user_id if user_id != "anonymous" else None)

    # Log request details with structured fields
    log.info(
        "HTTP request processed",
        extra={
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "latency_ms": round(latency_ms, 2),
            "client_host": request.client.host if request.client else None,
            "user_id": user_id,
        },
    )

    return response
