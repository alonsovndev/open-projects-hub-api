"""Storage port for user-owned provider API keys."""

from abc import ABC, abstractmethod

from src.app.features.ai_config.domain.entities.user_api_key_entity import UserApiKeyEntity
from src.app.features.ai_config.domain.value_objects.ai_provider import AIProvider
from src.app.shared.domain.value_objects.entity_id import EntityId


class UserApiKeyRepository(ABC):
    """Persistence for `UserApiKeyEntity`, one key per user per provider."""

    @abstractmethod
    async def find_by_user(self, user_id: EntityId) -> list[UserApiKeyEntity]:
        """Return every key the user has configured, ordered by provider."""

    @abstractmethod
    async def find_by_user_and_provider(self, user_id: EntityId, provider: AIProvider) -> UserApiKeyEntity | None:
        """Return the user's key for one provider, or None if they have not configured it."""

    @abstractmethod
    async def upsert(self, api_key: UserApiKeyEntity) -> UserApiKeyEntity:
        """
        Insert the key, or replace the secret on the user's existing key for that provider.

        Replacing in place is what makes a rotated key unusable immediately: there is no
        second row holding the previous ciphertext.
        """

    @abstractmethod
    async def delete(self, user_id: EntityId, provider: AIProvider) -> bool:
        """
        Hard-delete the user's key for a provider.

        NFR-010-04 requires the key material to be gone, not flagged, so implementations
        must issue a real DELETE.

        Returns:
            True if a key was removed, False if there was nothing to remove.
        """
