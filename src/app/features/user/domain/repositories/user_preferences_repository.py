"""
UserPreferencesRepository interface - domain layer.
"""

from abc import ABC, abstractmethod

from src.app.features.user.domain.entities.user_preferences_entity import UserPreferencesEntity
from src.app.shared.domain.value_objects.entity_id import EntityId


class UserPreferencesRepository(ABC):
    """Repository interface for user preferences persistence."""

    @abstractmethod
    async def find_by_user_id(self, user_id: EntityId) -> UserPreferencesEntity | None:
        """
        Find preferences by user ID.

        Args:
            user_id: User entity ID

        Returns:
            UserPreferencesEntity if found, None otherwise
        """

    @abstractmethod
    async def save(self, preferences: UserPreferencesEntity) -> UserPreferencesEntity | None:
        """
        Save or update user preferences.

        Args:
            preferences: UserPreferencesEntity to save

        Returns:
            Saved UserPreferencesEntity, or None if save failed
        """

    @abstractmethod
    async def delete_by_user_id(self, user_id: EntityId) -> bool:
        """
        Delete preferences by user ID.

        Args:
            user_id: User entity ID

        Returns:
            True if deleted, False otherwise
        """
