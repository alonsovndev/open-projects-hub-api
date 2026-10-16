"""Deny-by-default guard over the whole route table (US-EP4-BE-001).

This is the RBAC rule set in executable form. Per-endpoint tests prove the guards that
exist behave correctly; this one proves no route ships *without* a guard, so a new
unguarded mutation fails the suite instead of reaching production unnoticed.

Adding an entry to any allowlist below is a security decision, not a formality:
`_PUBLIC_ROUTES` opens a route to anonymous callers and `_SELF_SERVICE_ROUTES` lets any
signed-in user write.

Tenant isolation is checked here too: every route under a tenant prefix must resolve the
caller's workspace from the token (`get_request_context`), because that is the only
source of the workspace the use cases filter by.
"""

from fastapi.routing import APIRoute

from src.app.app import fastapi_app
from src.app.features.auth.presentation.auth_routes import logout_principal
from src.app.shared.presentation.auth_dependencies import (
    get_current_user,
    get_request_context,
    require_admin,
    require_editor,
)


_MUTATING_METHODS = frozenset({"POST", "PUT", "PATCH", "DELETE"})

# Reachable without a token: liveness probes, the auth handshake itself (a caller cannot
# authenticate before it has logged in) and the Client Review page, whose access code is its
# only credential. Keyed by (method, path) so that adding a different verb on the same path
# does not silently inherit the exemption.
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
        ("GET", "/v1/viewer/{access_code}"),
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

# Only a workspace's Admin may add people to it.
_ADMIN_ONLY_ROUTES = frozenset({("POST", "/v1/users")})

# Routes that read or write workspace data. Each must take its workspace from the token.
_TENANT_PREFIXES = (
    "/v1/clients",
    "/v1/projects",
    "/v1/stories",
    "/v1/refinement",
    "/v1/dashboard",
    "/v1/users",
)
# Account-level routes under /v1/users that act only on the caller's own record.
_ACCOUNT_ROUTES = frozenset(
    {
        ("GET", "/v1/users/me/profile"),
        ("PATCH", "/v1/users/me/profile"),
        ("POST", "/v1/users/me/password"),
    }
)
_ROLE_GUARDS = {require_admin, require_editor}


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
            if (method, path) not in _PUBLIC_ROUTES
            and not {get_current_user, get_request_context} & _dependency_calls(route)
            and not ((method, path) == ("POST", "/v1/auth/logout") and logout_principal in _dependency_calls(route))
        )

        assert unguarded == [], f"Routes reachable without authentication: {unguarded}"

    def test_conditional_cookie_guard_is_limited_to_logout(self):
        guarded = {
            (method, path) for method, path, route in _route_methods() if logout_principal in _dependency_calls(route)
        }
        assert guarded == {("POST", "/v1/auth/logout")}

    def test_every_mutating_route_requires_a_role_guard(self):
        unguarded_writes = sorted(
            f"{method} {path}"
            for method, path, route in _route_methods()
            if method in _MUTATING_METHODS
            and (method, path) not in _PUBLIC_ROUTES
            and (method, path) not in _SELF_SERVICE_ROUTES
            and not _ROLE_GUARDS & _dependency_calls(route)
        )

        assert unguarded_writes == [], f"Mutating routes with no role guard: {unguarded_writes}"

    def test_admin_only_routes_require_admin(self):
        non_admin_reachable = sorted(
            f"{method} {path}"
            for method, path, route in _route_methods()
            if (method, path) in _ADMIN_ONLY_ROUTES and require_admin not in _dependency_calls(route)
        )

        assert non_admin_reachable == [], f"Admin-only routes a Member could reach: {non_admin_reachable}"

    def test_public_routes_other_than_health_and_auth_are_read_only(self):
        """An anonymous caller must never be able to write workspace data."""
        public_writes = sorted(
            f"{method} {path}"
            for method, path in _PUBLIC_ROUTES
            if method in _MUTATING_METHODS and not path.startswith("/v1/auth/")
        )

        assert public_writes == [], f"Public routes that write: {public_writes}"

    def test_every_tenant_route_takes_its_workspace_from_the_token(self):
        """A tenant route without the request context would have no workspace to filter by."""
        unscoped = sorted(
            f"{method} {path}"
            for method, path, route in _route_methods()
            if path.startswith(_TENANT_PREFIXES)
            and (method, path) not in _ACCOUNT_ROUTES
            and get_request_context not in _dependency_calls(route)
        )

        assert unscoped == [], f"Tenant routes not scoped to the caller's workspace: {unscoped}"

    def test_allowlists_do_not_name_routes_that_no_longer_exist(self):
        """A stale allowlist entry silently re-opens a route if the path is ever reused."""
        existing = {(method, path) for method, path, _ in _route_methods()}

        stale = sorted(
            f"{method} {path}"
            for method, path in (_PUBLIC_ROUTES | _SELF_SERVICE_ROUTES | _ADMIN_ONLY_ROUTES | _ACCOUNT_ROUTES)
            if (method, path) not in existing
        )

        assert stale == [], f"Allowlists name routes that do not exist: {stale}"
