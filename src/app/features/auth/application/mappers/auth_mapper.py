"""Mapper for auth DTOs."""

from datetime import UTC, datetime

from src.app.features.auth.application.dtos.auth_dto import AdminLoginResponse, UserDetail
from src.app.features.user.domain.entities.user_entity import UserEntity


def to_admin_login_response(user_entity: UserEntity, token: str, refresh_token: str) -> AdminLoginResponse:
    """
    Convert a UserEntity and tokens to an AdminLoginResponse DTO.

    Args:
        user_entity: UserEntity instance
        token: Generated JWT access token
        refresh_token: Generated JWT refresh token

    Returns:
        AdminLoginResponse instance
    """
    display_name = user_entity.display_name
    logged_in_at = datetime.now(tz=UTC).isoformat().replace("+00:00", "Z")

    return AdminLoginResponse(
        token=token,
        access_token=token,
        refresh_token=refresh_token,
        email=str(user_entity.email),
        display_name=display_name,
        logged_in_at=logged_in_at,
        role=str(user_entity.role.value),
        user=UserDetail(
            email=str(user_entity.email),
            display_name=display_name,
            name=display_name,
            role=str(user_entity.role.value),
        ),
    )
