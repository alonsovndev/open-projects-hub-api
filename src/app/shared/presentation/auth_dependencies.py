"""
Authentication and authorization dependencies for FastAPI routes.

This module provides reusable dependency functions for:
- JWT token validation and user extraction
- Role-based access control (RBAC)
- Resource-level authorization (ownership checks)
"""

from collections.abc import Awaitable, Callable
from typing import Any

import jwt
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from src.app.composition.infrastructure import get_jwt_handler
from src.app.features.auth.domain.exceptions.auth_exceptions import UnauthorizedError
from src.app.features.user.domain.value_objects.user_role import UserRole
from src.app.shared.application.request_context import RequestContext
from src.app.shared.domain.value_objects.entity_id import EntityId
from src.app.shared.infrastructure.security.jwt_handler import JWTHandler


# auto_error would answer a missing Authorization header with 403, which the API contract
# reserves for "role not allowed". We raise the 401 ourselves instead.
security = HTTPBearer(auto_error=False)


async def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    jwt_handler: JWTHandler = Depends(get_jwt_handler),
) -> dict[str, Any]:
    """
    Dependency to extract and validate JWT token from Authorization header.

    Returns user claims from token payload and sets user_id in request state
    for logging purposes.

    Raises:
        HTTPException: 401 if the token is missing, invalid, or expired
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        token = credentials.credentials
        payload = jwt_handler.decode_access_token(token)

        if not payload.get("sub") or not payload.get("email"):
            raise UnauthorizedError("Invalid token payload")

        # Set user_id in request state for logging middleware
        request.state.user_id = payload.get("sub")

        return payload

    except jwt.PyJWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        ) from e
    except UnauthorizedError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        ) from e


async def get_request_context(
    current_user: dict[str, Any] = Depends(get_current_user),
) -> RequestContext:
    """
    The caller's identity and workspace, taken only from the verified token.

    Tenant-scoped routes depend on this so the workspace can never come from the path or
    body. Tokens minted before workspaces existed carry no `wid`; they get a 401 and the
    client's refresh flow issues a new one.

    Raises:
        HTTPException: 401 if the token has no valid workspace or role claim
    """
    try:
        return RequestContext(
            user_id=EntityId.from_string(str(current_user["sub"])),
            workspace_id=EntityId.from_string(str(current_user["wid"])),
            role=UserRole(current_user["role"]),
        )
    except (KeyError, ValueError) as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"},
        ) from e


def require_roles(*allowed_roles: UserRole) -> Callable[..., Awaitable[RequestContext]]:
    """Build a dependency that admits only the given roles (403 otherwise)."""

    async def dependency(ctx: RequestContext = Depends(get_request_context)) -> RequestContext:
        if ctx.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )
        return ctx

    return dependency


# Bound once at import time: the route-policy test identifies guards by object identity.
require_admin = require_roles(UserRole.ADMIN)
require_editor = require_roles(UserRole.ADMIN, UserRole.MEMBER)
