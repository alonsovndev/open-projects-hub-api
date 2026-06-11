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

from src.app.composition import get_database_session
from src.app.composition.infrastructure import get_jwt_handler
from src.app.features.auth.domain.exceptions.auth_exceptions import UnauthorizedError
from src.app.features.user.domain.value_objects.user_role import UserRole
from src.app.shared.application.authorization.story_authorization_service import StoryAuthorizationService
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


def create_story_owner_or_admin_dependency(story_id: str):
    """
    Factory function to create a story owner/admin check dependency.

    This factory pattern is used because the story_id comes from path parameters
    and needs to be available at dependency resolution time. FastAPI's Depends()
    doesn't work with closures that need runtime path parameters, so we manually
    consume the database session generator.

    Args:
        story_id: Story UUID as string from path parameter

    Returns:
        Dependency function that validates authorization
    """

    async def require_story_owner_or_admin_impl(
        current_user: dict[str, Any] = Depends(get_current_user),
    ) -> dict[str, Any]:
        """
        Verify user is story owner or admin.

        Raises:
            HTTPException: 403 if user is not authorized
            HTTPException: 404 if story not found
            HTTPException: 400 if story_id is invalid
        """
        try:
            user_id: str = current_user.get("sub")  # type: ignore[assignment]
            user_role: str = current_user.get("role")  # type: ignore[assignment]

            # Use authorization service to check permissions
            async for session in get_database_session():
                is_authorized, error_detail = await StoryAuthorizationService.is_story_owner_or_admin(
                    session=session,
                    story_id=story_id,
                    user_id=user_id,
                    user_role=user_role,
                )

                if not is_authorized:
                    # Determine status code based on error type
                    if error_detail == "Story not found":
                        raise HTTPException(
                            status_code=status.HTTP_404_NOT_FOUND,
                            detail=error_detail,
                        )
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=error_detail,
                    )

                return current_user

            # Should not reach here, but satisfy type checker
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Database session error",
            )

        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid story ID format",
            ) from e
        except HTTPException:
            raise

    return require_story_owner_or_admin_impl
