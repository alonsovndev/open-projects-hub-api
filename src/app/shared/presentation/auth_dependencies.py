"""
Authentication and authorization dependencies for FastAPI routes.

This module provides reusable dependency functions for:
- JWT token validation and user extraction
- Role-based access control (RBAC)
- Resource-level authorization (ownership checks)
"""

from typing import Any

import jwt
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from src.app.composition.infrastructure import get_jwt_handler
from src.app.features.auth.domain.exceptions.auth_exceptions import UnauthorizedError
from src.app.features.user.domain.value_objects.user_role import UserRole
from src.app.shared.infrastructure.security.jwt_handler import JWTHandler


security = HTTPBearer()


async def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    jwt_handler: JWTHandler = Depends(get_jwt_handler),
) -> dict[str, Any]:
    """
    Dependency to extract and validate JWT token from Authorization header.

    Returns user claims from token payload and sets user_id in request state
    for logging purposes.

    Raises:
        HTTPException: 401 if token is invalid or expired
    """
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


async def require_admin(
    current_user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, Any]:
    """
    Dependency to verify user has ADMIN role.

    Returns user claims if admin, raises 403 otherwise.

    Raises:
        HTTPException: 403 if user is not an admin
    """
    user_role = current_user.get("role")

    if user_role != UserRole.ADMIN.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions",
        )

    return current_user
