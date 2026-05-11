from src.app.features.user.domain.entities.user_entity import UserEntity
from src.app.features.user.infrastructure.models.user_model import UserModel


def map_model_to_entity(user_model: UserModel) -> UserEntity:
    """Maps a user model to a user entity."""

    return UserEntity(
        id=user_model.id,
        email=user_model.email,
        display_name=user_model.display_name,
        password_hash=user_model.password_hash,
        role=user_model.role,
        created_at=user_model.created_at,
        updated_at=user_model.updated_at,
    )
