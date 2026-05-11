"""
UserPreferences entity - represents user preferences and settings.
"""
from dataclasses import dataclass

from src.app.features.user.domain.value_objects.theme import Theme
from src.app.shared.domain.value_objects.entity_id import EntityId


@dataclass
class UserPreferencesEntity:
    """
    UserPreferences entity - represents user settings.
    
    Attributes:
        id: Unique identifier
        user_id: Reference to user
        theme: Theme preference (light, dark, auto)
        language: ISO language code
    """

    id: EntityId
    user_id: EntityId
    theme: Theme
    language: str

    @staticmethod
    def create_default(user_id: EntityId) -> "UserPreferencesEntity":
        """
        Factory method to create default preferences for a user.
        
        Args:
            user_id: User entity ID
            
        Returns:
            UserPreferencesEntity with default values
        """
        return UserPreferencesEntity(
            id=EntityId.generate(),
            user_id=user_id,
            theme=Theme.AUTO,
            language="en",
        )

    def update_theme(self, theme: Theme) -> "UserPreferencesEntity":
        """Update theme preference."""
        self.theme = theme
        return self

    def update_language(self, language: str) -> "UserPreferencesEntity":
        """Update language preference."""
        self.language = language
        return self
