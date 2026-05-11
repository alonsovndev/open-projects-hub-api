"""
GetUserPreferencesUseCase - retrieve user preferences with default fallback.
"""
from src.app.features.user.domain.entities.user_preferences_entity import UserPreferencesEntity
from src.app.features.user.domain.repositories.user_preferences_repository import UserPreferencesRepository
from src.app.shared.domain.value_objects.entity_id import EntityId
from src.app.shared.utils.log_util import log


class GetUserPreferencesUseCase:
    """
    Use case for retrieving user preferences.
    
    Returns default preferences if none exist (create-on-read pattern).
    """

    def __init__(self, preferences_repository: UserPreferencesRepository):
        self.preferences_repository = preferences_repository

    async def execute(self, user_id: EntityId) -> UserPreferencesEntity:
        """
        Get user preferences, creating default if not found.
        
        Args:
            user_id: User entity ID
            
        Returns:
            UserPreferencesEntity (existing or newly created default)
        """
        # Try to find existing preferences
        preferences = await self.preferences_repository.find_by_user_id(user_id)

        if preferences:
            log.info(f"Found existing preferences for user {user_id.value}")
            return preferences

        # Create default preferences
        log.info(f"Creating default preferences for user {user_id.value}")
        default_preferences = UserPreferencesEntity.create_default(user_id)
        
        # Persist default preferences
        saved_preferences = await self.preferences_repository.save(default_preferences)
        
        if saved_preferences:
            return saved_preferences
        
        # If save failed, return in-memory default (shouldn't happen in normal flow)
        log.warning(f"Failed to persist default preferences for user {user_id.value}, returning in-memory default")
        return default_preferences
