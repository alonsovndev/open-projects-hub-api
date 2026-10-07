"""Remove a user's provider API key."""

from src.app.features.ai_config.domain.exceptions.ai_config_exceptions import ApiKeyNotFoundError
from src.app.features.ai_config.domain.repositories.user_api_key_repository import UserApiKeyRepository
from src.app.features.ai_config.domain.value_objects.ai_provider import AIProvider
from src.app.shared.domain.value_objects.entity_id import EntityId
from src.app.shared.logging import get_logger, set_user_id


class DeleteApiKeyUseCase:
    """
    Hard-deletes a provider key (FR-010-09, NFR-010-04).

    What happens to refinement afterwards is decided at refinement time, not here: the
    provider resolver falls back to platform credits when any remain, and blocks with the
    add-a-key prompt when none do. Encoding that here would duplicate the rule.
    """

    def __init__(self, repository: UserApiKeyRepository):
        """
        Args:
            repository: Storage for user provider keys.
        """
        self._repository = repository

    async def execute(self, provider: AIProvider, user_id: str) -> None:
        """
        Delete the caller's key for a provider.

        Args:
            provider: The provider whose key should be removed.
            user_id: The authenticated user's UUID string.

        Raises:
            ApiKeyNotFoundError: If the user has no key for that provider.
        """
        log = get_logger(__name__)
        set_user_id(user_id)

        deleted = await self._repository.delete(EntityId.from_string(user_id), provider)

        if not deleted:
            raise ApiKeyNotFoundError(provider)

        log.info(
            "Provider API key deleted",
            extra={"event_type": "ai_config.key.deleted", "provider": provider.value},
        )
