from src.app.features.domain.entities.user_entity import UserEntity
from src.app.features.infrastructure.models.user_model import UserModel


def map_model_to_entity(user_model: UserModel):
    """Maps a user model to a user entity."""

    return UserEntity(
        id=user_model.id,
        email=user_model.email,
        first_name=user_model.first_name,
        last_name=user_model.last_name,
        password_hash=user_model.password_hash,
        created_at=user_model.created_at,
        updated_at=user_model.updated_at,
    )
