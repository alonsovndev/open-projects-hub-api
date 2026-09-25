"""Entity to DTO mapping for provider API keys."""

from src.app.features.ai_config.application.dtos.ai_config_dto import ApiKeyResponse, ListApiKeysResponse
from src.app.features.ai_config.domain.entities.user_api_key_entity import UserApiKeyEntity


def to_api_key_response(entity: UserApiKeyEntity) -> ApiKeyResponse:
    """Describe a stored key without exposing its secret."""
    return ApiKeyResponse(
        provider=entity.provider,
        masked_key=entity.masked_key,
        configured_at=entity.created_at,
        last_validated_at=entity.last_validated_at,
    )


def to_list_api_keys_response(entities: list[UserApiKeyEntity]) -> ListApiKeysResponse:
    """Describe every key a user has configured."""
    return ListApiKeysResponse(keys=[to_api_key_response(entity) for entity in entities])
