"""Assign story use case."""
from typing import Optional

from src.app.features.stories.application.dtos.story_dto import StoryResponse
from src.app.features.stories.domain.entities.story_entity import StoryEntity
from src.app.features.stories.domain.repositories.story_repository import StoryRepository
from src.app.shared.domain.value_objects.entity_id import EntityId
from src.app.features.stories.application.mappers.story_mapper import to_story_response


class AssignStoryUseCase:
    """Use case for assigning a story to a user."""
    
    def __init__(self, story_repository: StoryRepository):
        """
        Initialize use case.
        
        Args:
            story_repository: Story repository
        """
        self._repository = story_repository
    
    async def execute(self, story_id: str, user_id: str) -> Optional[StoryResponse]:
        """
        Execute assign story use case.
        
        Args:
            story_id: Story UUID
            user_id: User UUID to assign
            
        Returns:
            StoryResponse if found and assigned, None otherwise
            
        Raises:
            ValueError: If validation fails
        """
        from uuid import UUID
        
        entity = await self._repository.find_by_id(UUID(story_id))
        
        if not entity:
            return None
        
        entity.assign_to(EntityId.from_string(user_id))
        
        saved_entity = await self._repository.save(entity)
        
        if not saved_entity:
            raise ValueError("Failed to assign story")
        
        return to_story_response(saved_entity)