"""Delete story use case."""
from uuid import UUID

from src.app.features.stories.domain.repositories.story_repository import StoryRepository


class DeleteStoryUseCase:
    """Use case for deleting a story."""
    
    def __init__(self, story_repository: StoryRepository):
        """
        Initialize use case.
        
        Args:
            story_repository: Story repository
        """
        self._repository = story_repository
    
    async def execute(self, story_id: str) -> bool:
        """
        Execute delete story use case.
        
        Args:
            story_id: Story UUID
            
        Returns:
            True if deleted, False if not found
        """
        deleted = await self._repository.delete(UUID(story_id))
        return deleted