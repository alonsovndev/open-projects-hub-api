from src.app.features.user.domain.entities.user_entity import UserEntity
from src.app.features.user.domain.value_objects.email import Email
from src.app.features.user.domain.value_objects.user_role import UserRole
from src.app.features.user.infrastructure.models.user_model import UserModel
from src.app.shared.domain.value_objects.entity_id import EntityId


def map_model_to_entity(user_model: UserModel) -> UserEntity:
    """Maps a user model to a user entity."""

    return UserEntity(
        id=EntityId(user_model.id),
        email=Email(user_model.email),
        display_name=user_model.display_name,
        password_hash=user_model.password_hash,
        role=UserRole(user_model.role),
        created_at=user_model.created_at,
        updated_at=user_model.updated_at,
    )
