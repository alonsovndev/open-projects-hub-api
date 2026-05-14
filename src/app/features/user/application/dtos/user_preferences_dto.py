"""
DTOs for user preferences endpoints.

Handles request/response models for GET and PATCH /user/preferences.
"""
from typing import Optional
from pydantic import BaseModel, ConfigDict, field_validator
from pydantic.alias_generators import to_camel


class UserPreferencesResponse(BaseModel):
    """Response model for user preferences."""
    
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )
    
    id: str
    user_id: str
    theme: str
    language: str


class UpdatePreferencesRequest(BaseModel):
    """Request model for updating user preferences (partial update)."""
    
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )
    
    theme: Optional[str] = None
    language: Optional[str] = None
    
    @field_validator("theme")
    @classmethod
    def validate_theme(cls, theme_value: Optional[str]) -> Optional[str]:
        """
        Validate theme value.
        
        Args:
            theme_value: Theme string
            
        Returns:
            Validated theme
            
        Raises:
            ValueError: If theme is not valid
        """
        if theme_value is not None:
            valid_themes = ["light", "dark", "auto"]
            if theme_value not in valid_themes:
                raise ValueError(f"Invalid theme. Must be one of: {', '.join(valid_themes)}")
        return theme_value
    
    @field_validator("language")
    @classmethod
    def validate_language(cls, language_value: Optional[str]) -> Optional[str]:
        """
        Validate language code (basic validation).
        
        Args:
            language_value: Language code
            
        Returns:
            Validated language code
            
        Raises:
            ValueError: If language code is invalid
        """
        if language_value is not None:
            if len(language_value) < 2 or len(language_value) > 10:
                raise ValueError("Language code must be between 2 and 10 characters")
        return language_value
