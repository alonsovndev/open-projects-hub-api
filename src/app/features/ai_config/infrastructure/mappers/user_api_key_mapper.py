"""Mapper between UserApiKeyEntity and UserApiKeyModel."""

from src.app.features.ai_config.domain.entities.user_api_key_entity import UserApiKeyEntity
from src.app.features.ai_config.domain.value_objects.ai_provider import AIProvider
from src.app.features.ai_config.infrastructure.models.user_api_key_model import UserApiKeyModel
from src.app.shared.domain.value_objects.entity_id import EntityId


class UserApiKeyMapper:
    """Maps between UserApiKeyEntity and UserApiKeyModel."""

    @staticmethod
    def to_entity(model: UserApiKeyModel) -> UserApiKeyEntity:
        """Convert UserApiKeyModel to UserApiKeyEntity."""
        return UserApiKeyEntity(
            id=EntityId(model.id),
            user_id=EntityId(model.user_id),
            provider=AIProvider(model.provider),
            ciphertext=model.encrypted_key,
            nonce=model.encryption_nonce,
            key_version=model.key_version,
            masked_key=model.masked_key,
            last_validated_at=model.last_validated_at,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    @staticmethod
    def to_model(entity: UserApiKeyEntity) -> UserApiKeyModel:
        """Convert UserApiKeyEntity to UserApiKeyModel."""
        return UserApiKeyModel(
            id=entity.id.value,
            user_id=entity.user_id.value,
            provider=entity.provider.value,
            encrypted_key=entity.ciphertext,
            encryption_nonce=entity.nonce,
            key_version=entity.key_version,
            masked_key=entity.masked_key,
            last_validated_at=entity.last_validated_at,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )
