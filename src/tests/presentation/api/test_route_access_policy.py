"""Deny-by-default guard over the whole route table (US-EP4-BE-001).

This is the RBAC rule set in executable form. Per-endpoint tests prove the guards that
exist behave correctly; this one proves no route ships *without* a guard, so a new
unguarded mutation fails the suite instead of reaching production unnoticed.

Adding an entry to either allowlist below is a security decision, not a formality:
`_PUBLIC_ROUTES` opens a route to anonymous callers, and `_SELF_SERVICE_ROUTES` lets a
Viewer write.
"""

from fastapi.routing import APIRoute

from src.app.app import fastapi_app
from src.app.shared.presentation.auth_dependencies import get_current_user, require_admin


_MUTATING_METHODS = frozenset({"POST", "PUT", "PATCH", "DELETE"})

# Reachable without a token: liveness probes, the OpenAPI schema, and the auth handshake
# itself (a caller cannot authenticate before it has logged in).
_PUBLIC_ROUTES = frozenset(
    {
        "/",
        "/health",
        "/health/live",
        "/health/ready",
        "/v1/auth/login",
        "/v1/auth/register",
        "/v1/auth/refresh",
        "/v1/auth/forgot-password",
        "/v1/auth/resend-reset-code",
        "/v1/auth/reset-password",
    }
)

# Mutations any authenticated user may perform, because they only touch that user's own
# account. Nothing project-related belongs here.
_SELF_SERVICE_ROUTES = frozenset(
    {
        ("POST", "/v1/auth/logout"),
        ("PATCH", "/v1/users/me/profile"),
        ("POST", "/v1/users/me/password"),
    }
)


def _dependency_calls(route: APIRoute) -> set[object]:
    """Every dependency callable reachable from the route, including nested ones."""
    collected: set[object] = set()
    pending = list(route.dependant.dependencies)

    while pending:
        dependency = pending.pop()
        if dependency.call is not None:
            collected.add(dependency.call)
        pending.extend(dependency.dependencies)

    return collected


def _api_routes() -> list[APIRoute]:
    return [route for route in fastapi_app.routes if isinstance(route, APIRoute)]


class TestRouteAccessPolicy:
    def test_every_route_is_public_by_decision_or_authenticated(self):
        unguarded = sorted(
            f"{method} {route.path}"
            for route in _api_routes()
            for method in sorted(route.methods)
            if route.path not in _PUBLIC_ROUTES and not {get_current_user, require_admin} & _dependency_calls(route)
        )

        assert unguarded == [], f"Routes reachable without authentication: {unguarded}"

    def test_every_mutating_route_requires_admin(self):
        viewer_writable = sorted(
            f"{method} {route.path}"
            for route in _api_routes()
            for method in sorted(route.methods & _MUTATING_METHODS)
            if route.path not in _PUBLIC_ROUTES
            and (method, route.path) not in _SELF_SERVICE_ROUTES
            and require_admin not in _dependency_calls(route)
        )

        assert viewer_writable == [], f"Mutating routes a Viewer could reach: {viewer_writable}"

    def test_allowlists_do_not_name_routes_that_no_longer_exist(self):
        """A stale allowlist entry silently re-opens a route if the path is ever reused."""
        existing_paths = {route.path for route in _api_routes()}
        existing_pairs = {(method, route.path) for route in _api_routes() for method in route.methods}

        stale_public = sorted(path for path in _PUBLIC_ROUTES if path not in existing_paths)
        stale_self_service = sorted(
            f"{method} {path}" for method, path in _SELF_SERVICE_ROUTES if (method, path) not in existing_pairs
        )

        assert stale_public == [], f"Public allowlist names missing routes: {stale_public}"
        assert stale_self_service == [], f"Self-service allowlist names missing routes: {stale_self_service}"
