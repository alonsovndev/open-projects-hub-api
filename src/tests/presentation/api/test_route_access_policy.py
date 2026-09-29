"""Deny-by-default guard over the whole route table (US-EP4-BE-001).

This is the RBAC rule set in executable form. Per-endpoint tests prove the guards that
exist behave correctly; this one proves no route ships *without* a guard, so a new
unguarded mutation fails the suite instead of reaching production unnoticed.

Adding an entry to any allowlist below is a security decision, not a formality:
`_PUBLIC_ROUTES` opens a route to anonymous callers and `_SELF_SERVICE_ROUTES` lets a
Viewer write, while removing one from `_ADMIN_ONLY_READS` exposes that data to Viewers.
"""

from fastapi.routing import APIRoute

from src.app.app import fastapi_app
from src.app.shared.presentation.auth_dependencies import get_current_user, require_admin


_MUTATING_METHODS = frozenset({"POST", "PUT", "PATCH", "DELETE"})

# Reachable without a token: liveness probes and the auth handshake itself (a caller
# cannot authenticate before it has logged in). Keyed by (method, path) so that adding a
# different verb on the same path does not silently inherit the exemption.
_PUBLIC_ROUTES = frozenset(
    {
        ("GET", "/"),
        ("GET", "/health"),
        ("GET", "/health/live"),
        ("GET", "/health/ready"),
        ("POST", "/v1/auth/login"),
        ("POST", "/v1/auth/register"),
        ("POST", "/v1/auth/refresh"),
        ("POST", "/v1/auth/forgot-password"),
        ("POST", "/v1/auth/resend-reset-code"),
        ("POST", "/v1/auth/reset-password"),
        ("POST", "/v1/auth/verify-email"),
        ("POST", "/v1/auth/resend-verification"),
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

# Reads a Viewer must not reach. The mutation rule above cannot express these: a GET is
# not a write, but client records are the freelancer's other business relationships.
_ADMIN_ONLY_READS = frozenset(
    {
        ("GET", "/v1/clients"),
        ("GET", "/v1/clients/{client_id}"),
        ("GET", "/v1/refinement/projects/{project_id}/drafts"),
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


def _route_methods() -> list[tuple[str, str, APIRoute]]:
    return [(method, route.path, route) for route in _api_routes() for method in sorted(route.methods)]


class TestRouteAccessPolicy:
    def test_every_route_is_public_by_decision_or_authenticated(self):
        unguarded = sorted(
            f"{method} {path}"
            for method, path, route in _route_methods()
            if (method, path) not in _PUBLIC_ROUTES and not {get_current_user, require_admin} & _dependency_calls(route)
        )

        assert unguarded == [], f"Routes reachable without authentication: {unguarded}"

    def test_every_mutating_route_requires_admin(self):
        viewer_writable = sorted(
            f"{method} {path}"
            for method, path, route in _route_methods()
            if method in _MUTATING_METHODS
            and (method, path) not in _PUBLIC_ROUTES
            and (method, path) not in _SELF_SERVICE_ROUTES
            and require_admin not in _dependency_calls(route)
        )

        assert viewer_writable == [], f"Mutating routes a Viewer could reach: {viewer_writable}"

    def test_admin_only_reads_require_admin(self):
        """Read authorization is not implied by the mutation rule, so it is listed explicitly."""
        viewer_readable = sorted(
            f"{method} {path}"
            for method, path, route in _route_methods()
            if (method, path) in _ADMIN_ONLY_READS and require_admin not in _dependency_calls(route)
        )

        assert viewer_readable == [], f"Admin-only reads a Viewer could reach: {viewer_readable}"

    def test_allowlists_do_not_name_routes_that_no_longer_exist(self):
        """A stale allowlist entry silently re-opens a route if the path is ever reused."""
        existing = {(method, path) for method, path, _ in _route_methods()}

        stale = sorted(
            f"{method} {path}"
            for method, path in _PUBLIC_ROUTES | _SELF_SERVICE_ROUTES | _ADMIN_ONLY_READS
            if (method, path) not in existing
        )

        assert stale == [], f"Allowlists name routes that do not exist: {stale}"
