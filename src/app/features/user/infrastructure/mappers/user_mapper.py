"""Mapper between User entity and User model."""

from src.app.features.user.domain.entities.user_entity import UserEntity
from src.app.features.user.domain.value_objects.user_role import UserRole
from src.app.features.user.infrastructure.models.user_model import UserModel
from src.app.shared.domain.value_objects.email import Email
from src.app.shared.domain.value_objects.entity_id import EntityId


class UserMapper:
    """Maps between UserEntity and UserModel."""

    @staticmethod
    def to_entity(model: UserModel) -> UserEntity:
        """Convert UserModel to UserEntity."""
        return UserEntity(
            id=EntityId(model.id),
            email=Email(model.email),
            display_name=model.display_name,
            password_hash=model.password_hash,
            role=UserRole(model.role),
            token_version=model.token_version or 0,
            ai_credits_remaining=model.ai_credits_remaining,
            ai_credits_granted=model.ai_credits_granted,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    @staticmethod
    def to_model(entity: UserEntity) -> UserModel:
        """Convert UserEntity to UserModel."""
        return UserModel(
            id=entity.id.value,
            email=entity.email.value,
            display_name=entity.display_name,
            password_hash=entity.password_hash,
            role=entity.role.value,
            token_version=entity.token_version,
            ai_credits_remaining=entity.ai_credits_remaining,
            ai_credits_granted=entity.ai_credits_granted,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )
