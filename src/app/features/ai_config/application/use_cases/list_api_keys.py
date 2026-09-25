"""List the provider keys a user has configured."""

from src.app.features.ai_config.application.dtos.ai_config_dto import ListApiKeysResponse
from src.app.features.ai_config.application.mappers.api_key_mapper import to_list_api_keys_response
from src.app.features.ai_config.domain.repositories.user_api_key_repository import UserApiKeyRepository
from src.app.shared.domain.value_objects.entity_id import EntityId


class ListApiKeysUseCase:
    """Returns the caller's configured keys in masked form (FR-010-07)."""

    def __init__(self, repository: UserApiKeyRepository):
        """
        Args:
            repository: Storage for user provider keys.
        """
        self._repository = repository

    async def execute(self, user_id: str) -> ListApiKeysResponse:
        """
        List configured providers.

        Args:
            user_id: The authenticated user's UUID string.

        Returns:
            ListApiKeysResponse with one masked entry per configured provider.
        """
        keys = await self._repository.find_by_user(EntityId.from_string(user_id))
        return to_list_api_keys_response(keys)
