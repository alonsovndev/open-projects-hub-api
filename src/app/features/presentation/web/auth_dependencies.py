from functools import lru_cache
from typing import Any, Dict

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from src.app.config.app_config import AppConfig
from src.app.features.domain.exceptions.auth_exceptions import UnauthorizedError
from src.app.features.domain.value_objects.user_role import UserRole
from src.shared.infrastructure.security.jwt_handler import JWTHandler

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
