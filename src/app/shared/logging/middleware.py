"""ASGI middleware for request context logging.

Sets request_id (from X-Request-ID header or auto-generated UUID) and
user_id (from JWT sub claim if authenticated) into the logging context
so every log line within a request is correlated. Also echoes the
request_id back in the response X-Request-ID header.
"""

import uuid

from starlette.types import ASGIApp, Message, Receive, Scope, Send

from src.app.shared.logging.logging import clear_context, set_request_id, set_user_id


class RequestContextMiddleware:
    """Injects request_id and user_id into the logging context for each request.

    Must be registered as an ASGI middleware (via app.add_middleware) so it
    wraps the entire request lifecycle, including other HTTP middleware.
    """

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] not in ("http", "websocket"):
            await self.app(scope, receive, send)
            return

        # Extract or generate request_id
        headers = dict(scope.get("headers", []))
        request_id = headers.get(b"x-request-id", b"").decode("utf-8", errors="replace")
        if not request_id:
            # Truncated UUID for readability — e.g. "a1b2c3d4-e5f6"
            request_id = str(uuid.uuid4())[:12]

        set_request_id(request_id)

        # Extract user_id from scope state if auth middleware already set it
        # (e.g. via JWT dependency). Falls back to "-" (anonymous).
        user_id = scope.get("user_id")
        set_user_id(user_id)

        # Wrap send to inject X-Request-ID into response headers
        async def send_wrapper(message: Message) -> None:
            if message["type"] == "http.response.start":
                response_headers = list(message.get("headers", []))
                response_headers.append((b"x-request-id", request_id.encode("utf-8")))
                message["headers"] = response_headers
            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
        finally:
            clear_context()


# Backward-compatible alias for app.py imports
CorrelationIdMiddleware = RequestContextMiddleware
