from src.app.features.user.application.dtos.user_dto import UserCreateRequest, UserResponse
from src.app.features.user.domain.entities.user_entity import UserEntity
from src.app.features.user.domain.value_objects.user_role import UserRole


def to_user_response(user_entity: UserEntity) -> UserResponse:
    """
    Convert a User Entity to a User DTO (Data Transfer Object).
    """

    return UserResponse(
        id=str(user_entity.id),
        email=str(user_entity.email),
        display_name=user_entity.display_name,
        role=str(user_entity.role.value),
    )


def map_create_request_to_entity(payload: UserCreateRequest, password_hash: str) -> UserEntity:
    """
    Convert a UserCreateRequest DTO to a UserEntity.

    Args:
        payload: The user creation request with email, display_name, password, and optional role
        password_hash: The hashed password

    Returns:
        UserEntity with the specified or default role (viewer)
    """
    # Parse role from string to UserRole enum
    role = UserRole.ADMIN if payload.role == "admin" else UserRole.VIEWER

    return UserEntity.create(
        email=str(payload.email).lower().strip(),
        display_name=payload.display_name.strip(),
        password_hash=password_hash,
        role=role,
    )
