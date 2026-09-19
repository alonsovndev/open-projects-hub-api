"""Tests for RequestContextMiddleware (request_id context + response header)."""

import pytest
from starlette.applications import Starlette
from starlette.responses import PlainTextResponse
from starlette.routing import Route
from starlette.testclient import TestClient

from src.app.shared.logging.logging import _request_id_ctx, _user_id_ctx
from src.app.shared.logging.middleware import RequestContextMiddleware


def _make_app() -> Starlette:
    async def root(request):
        # Verify request_id is already in the logging context during the request
        rid = _request_id_ctx.get()
        return PlainTextResponse(f"rid={rid}")

    app = Starlette(routes=[Route("/", root)])
    app.add_middleware(RequestContextMiddleware)
    return app


@pytest.fixture
def app():
    return _make_app()


@pytest.fixture(autouse=True)
def _isolate_context():
    token_r = _request_id_ctx.set("-")
    token_u = _user_id_ctx.set("-")
    try:
        yield
    finally:
        _request_id_ctx.reset(token_r)
        _user_id_ctx.reset(token_u)


class TestRequestContextMiddleware:
    def test_echoes_client_provided_request_id(self, app):
        client = TestClient(app)
        response = client.get("/", headers={"X-Request-ID": "my-id-123"})
        assert response.headers["X-Request-ID"] == "my-id-123"

    def test_generates_request_id_when_not_provided(self, app):
        client = TestClient(app)
        response = client.get("/")
        assert "X-Request-ID" in response.headers
        assert len(response.headers["X-Request-ID"]) > 0
        # Truncated UUID contains a dash (e.g. "a1b2c3d4-e5f6")
        assert "-" in response.headers["X-Request-ID"]

    def test_request_id_in_context_during_request(self, app):
        client = TestClient(app)
        response = client.get("/", headers={"X-Request-ID": "in-ctx-1"})
        assert response.text == "rid=in-ctx-1"

    def test_context_cleared_after_request(self, app):
        client = TestClient(app)
        client.get("/", headers={"X-Request-ID": "temp-id"})
        assert _request_id_ctx.get() == "-"
        assert _user_id_ctx.get() == "-"

    def test_works_for_non_http_scopes(self, app):
        """Lifecycle events should pass through without modification."""
        client = TestClient(app)
        # Startup/shutdown triggered by context manager; just verify no error
        with client:
            pass

    def test_alias_correlation_id_middleware_points_to_request_context(self):
        from src.app.shared.logging.middleware import CorrelationIdMiddleware, RequestContextMiddleware

        assert CorrelationIdMiddleware is RequestContextMiddleware
