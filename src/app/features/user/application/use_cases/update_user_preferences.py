"""
UpdateUserPreferencesUseCase - partial update of user preferences.
"""

from src.app.features.user.domain.entities.user_preferences_entity import UserPreferencesEntity
from src.app.features.user.domain.repositories.user_preferences_repository import UserPreferencesRepository
from src.app.features.user.domain.value_objects.theme import Theme
from src.app.shared.domain.value_objects.entity_id import EntityId
from src.app.shared.logging import get_logger


log = get_logger(__name__)


class UpdateUserPreferencesUseCase:
    """
    Use case for updating user preferences.

    Supports partial updates - only provided fields are updated.
    """

    def __init__(self, preferences_repository: UserPreferencesRepository):
        self.preferences_repository = preferences_repository

    async def execute(
        self,
        user_id: EntityId,
        theme: Theme | None = None,
        language: str | None = None,
    ) -> UserPreferencesEntity | None:
        """
        Update user preferences (partial update).

        Args:
            user_id: User entity ID
            theme: Optional theme preference
            language: Optional language preference

        Returns:
            Updated UserPreferencesEntity, or None if update failed

        Raises:
            ValueError: If user has no preferences (should call GET first to create defaults)
        """
        # Find existing preferences
        preferences = await self.preferences_repository.find_by_user_id(user_id)

        if not preferences:
            log.warning(f"No preferences found for user {user_id.value}")
            raise ValueError(f"User preferences not found for user {user_id.value}")

        # Apply partial updates
        if theme is not None:
            preferences.update_theme(theme)
            log.info(f"Updated theme to {theme.value} for user {user_id.value}")

        if language is not None:
            preferences.update_language(language)
            log.info(f"Updated language to {language} for user {user_id.value}")

        # Save updated preferences
        updated_preferences = await self.preferences_repository.save(preferences)

        if not updated_preferences:
            log.error(f"Failed to save preferences for user {user_id.value}")
            return None

        log.info(f"Successfully updated preferences for user {user_id.value}")
        return updated_preferences
