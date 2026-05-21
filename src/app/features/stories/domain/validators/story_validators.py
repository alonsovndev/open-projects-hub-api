"""Shared validation logic for story domain."""
from typing import Optional


class StoryValidators:
    """Centralized validation rules for story entities and DTOs."""
    
    # Validation constants
    MAX_TITLE_LENGTH = 255
    MIN_POINTS = 0
    MAX_POINTS = 100
    
    @staticmethod
    def validate_title(title: str) -> None:
        """
        Validate story title.
        
        Args:
            title: Story title to validate
            
        Raises:
            ValueError: If title is invalid
        """
        if not title or not title.strip():
            raise ValueError("Story title cannot be empty")
        if len(title) > StoryValidators.MAX_TITLE_LENGTH:
            raise ValueError(f"Story title cannot exceed {StoryValidators.MAX_TITLE_LENGTH} characters")
    
    @staticmethod
    def validate_points(points: Optional[int]) -> None:
        """
        Validate story points to ensure reasonable estimation bounds.
        
        Args:
            points: Story points to validate
            
        Raises:
            ValueError: If points are invalid
        """
        if points is not None and points < StoryValidators.MIN_POINTS:
            raise ValueError(f"Story points cannot be negative")
        if points is not None and points > StoryValidators.MAX_POINTS:
            raise ValueError(f"Story points cannot exceed {StoryValidators.MAX_POINTS}")
