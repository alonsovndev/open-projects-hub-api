from src.app.features.user.application.dtos.user_dto import UserCreateRequest, UserResponse
from src.app.features.user.domain.entities.user_entity import UserEntity
from src.app.features.user.domain.value_objects.user_role import UserRole
from src.app.shared.domain.value_objects.entity_id import EntityId


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


def map_create_request_to_entity(payload: UserCreateRequest, password_hash: str, workspace_id: EntityId) -> UserEntity:
    """
    Convert a UserCreateRequest DTO to a member or viewer of the given workspace.

    Args:
        payload: The user creation request with email, display_name, password, and optional role
        password_hash: The hashed password
        workspace_id: The creating Admin's workspace; never taken from the request

    Returns:
        UserEntity with the requested role (member by default)
    """
    return UserEntity.create_workspace_member(
        email=str(payload.email).lower().strip(),
        display_name=payload.display_name.strip(),
        password_hash=password_hash,
        role=UserRole(payload.role or UserRole.MEMBER.value),
        workspace_id=workspace_id,
    )
