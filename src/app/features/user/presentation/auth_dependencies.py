from functools import lru_cache
from typing import Any, Dict

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from src.app.config.app_config import AppConfig
from src.app.features.user.domain.exceptions.auth_exceptions import UnauthorizedError
from src.app.features.user.domain.value_objects.user_role import UserRole
from src.app.shared.infrastructure.security.jwt_handler import JWTHandler
from src.app.shared.domain.value_objects.entity_id import EntityId

security = HTTPBearer()


@lru_cache(maxsize=1)
def get_jwt_handler() -> JWTHandler:
    """
    Dependency to get JWTHandler instance.
    Creates a cached singleton instance from config.
    """
    config = AppConfig.instance()
    secret_key = config.get_config("jwt.secret_key")
    algorithm = config.get_config("jwt.algorithm", "HS256")
    expiration = config.get_config("jwt.access_token_expire_minutes", 1440)

    if not secret_key:
        raise ValueError("JWT secret_key not configured")

    return JWTHandler(
        secret_key=secret_key,
        algorithm=algorithm,
        expiration_minutes=int(expiration),
    )


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    jwt_handler: JWTHandler = Depends(get_jwt_handler),
) -> Dict[str, Any]:
    """
    Dependency to extract and validate JWT token from Authorization header.

    Returns user claims from token payload.

    Raises:
        HTTPException: 401 if token is invalid or expired
    """
    try:
        token = credentials.credentials
        payload = jwt_handler.decode_access_token(token)

        if not payload.get("sub") or not payload.get("email"):
            raise UnauthorizedError("Invalid token payload")

        return payload

    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except UnauthorizedError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )


async def require_admin(
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> Dict[str, Any]:
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
    
    Args:
        story_id: Story UUID as string
        
    Returns:
        Dependency function that validates authorization
    """
    async def require_story_owner_or_admin_impl(
        current_user: Dict[str, Any] = Depends(get_current_user),
    ) -> Dict[str, Any]:
        """
        Verify user is story owner or admin.
        
        Raises:
            HTTPException: 403 if user is not authorized
            HTTPException: 404 if story not found
            HTTPException: 400 if story_id is invalid
        """

        # Admin bypass - admins can modify any story
        user_role = current_user.get("role")
        if user_role == UserRole.ADMIN.value:
            return current_user
        
        # Regular user - check ownership
        try:
            # Parse story ID
            story_entity_id = EntityId.from_string(story_id)
            
            # Get database session and repository
            from src.app.shared.presentation.dependencies import get_database_session
            from src.app.features.stories.infrastructure.repositories.story_repository_impl import StoryRepositoryImpl
            
            async for session in get_database_session():
                story_repo = StoryRepositoryImpl(session)
                story = await story_repo.find_by_id(story_entity_id)
                
                if not story:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="Story not found"
                    )
                
                # Check if current user is the creator
                user_id = current_user.get("sub")
                if story.created_by.value != user_id:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="Not authorized to modify this story. Only the creator or an admin can modify stories."
                    )
                
                return current_user
                
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid story ID format"
            )
        except HTTPException:
            raise
    
    return require_story_owner_or_admin_impl
