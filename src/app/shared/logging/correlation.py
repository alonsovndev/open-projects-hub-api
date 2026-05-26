"""Request correlation ID middleware and log filter."""

import logging
import uuid
from contextvars import ContextVar

from fastapi import Request


# Thread-safe request-scoped correlation ID storage
correlation_id: ContextVar[str] = ContextVar("correlation_id", default="")


class CorrelationIdFilter(logging.Filter):
    """Injects the current request's correlation_id into every log record."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = correlation_id.get() or "N/A"
        return True


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
