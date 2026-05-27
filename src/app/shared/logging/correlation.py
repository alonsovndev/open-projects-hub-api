"""Request correlation ID middleware and log filter with user context support."""

import logging
import uuid
from contextvars import ContextVar

from fastapi import Request


# Thread-safe request-scoped correlation ID storage
correlation_id: ContextVar[str] = ContextVar("correlation_id", default="")

# Thread-safe request-scoped authenticated user ID storage
user_id: ContextVar[str] = ContextVar("user_id", default="")


class CorrelationIdFilter(logging.Filter):
    """Injects the current request's correlation_id and user_id into every log record."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = correlation_id.get() or "N/A"
        record.user_id = user_id.get() or "anonymous"
        return True


def set_user_context(authenticated_user_id: str | None) -> None:
    """
    Set the authenticated user ID for the current request context.

    This should be called after JWT validation in authenticated endpoints
    to ensure all subsequent logs include the user_id.

    Args:
        authenticated_user_id: The user ID from JWT token (sub claim), or None for anonymous
    """
    if authenticated_user_id:
        user_id.set(authenticated_user_id)
    else:
        user_id.set("anonymous")


class CorrelationIdMiddleware:
    """FastAPI middleware that manages X-Request-ID correlation IDs.

    - Extracts X-Request-ID from incoming request headers (or generates a new UUID)
    - Sets the correlation_id contextvar so all log lines include it
    - Adds X-Request-ID to response headers
    """

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request = Request(scope, receive)
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))

        # Set correlation ID for this request
        token = correlation_id.set(request_id)

        async def send_with_header(message):
            if message["type"] == "http.response.start":
                headers = dict(message.get("headers", []))
                headers[b"x-request-id"] = request_id.encode()
                message["headers"] = list(headers.items())
            await send(message)

        try:
            await self.app(scope, receive, send_with_header)
        finally:
            correlation_id.reset(token)
