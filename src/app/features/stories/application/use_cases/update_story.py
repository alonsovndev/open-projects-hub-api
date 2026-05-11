"""Update story use case."""
from typing import Optional

from src.app.features.stories.application.dtos.story_dto import StoryResponse
from src.app.features.stories.domain.entities.story_entity import StoryEntity
from src.app.features.stories.domain.repositories.story_repository import StoryRepository
from src.app.features.stories.domain.value_objects.story_priority import StoryPriority
from src.app.features.stories.domain.value_objects.story_status import StoryStatus
from src.app.shared.domain.value_objects.entity_id import EntityId
from src.app.shared.infrastructure.mappers.story_mapper import to_story_response


class UpdateStoryUseCase:
    """Use case for updating a story."""
    
    def __init__(self, story_repository: StoryRepository):
        """
        Initialize use case.
        
        Args:
            story_repository: Story repository
        """
        self._repository = story_repository
    
    async def execute(
        self,
        story_id: str,
        title: Optional[str] = None,
        description: Optional[str] = None,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        points: Optional[int] = None,
    ) -> Optional[StoryResponse]:
        """
        Execute update story use case.
        
        Args:
            story_id: Story UUID
            title: New title (if provided)
            description: New description (if provided)
            status: New status (if provided)
            priority: New priority (if provided)
            points: New points (if provided)
            
        Returns:
            StoryResponse if found and updated, None otherwise
            
        Raises:
            ValueError: If validation fails
        """
        from uuid import UUID
        
        # Find existing story
        entity = await self._repository.find_by_id(UUID(story_id))
        
        if not entity:
            return None
        
        # Validate status
        story_status = None
        if status:
            try:
                story_status = StoryStatus(status.lower())
            except ValueError:
                raise ValueError(f"Invalid status '{status}'. Must be: todo, in_progress, done")
        
        # Validate priority
        story_priority = None
        if priority:
            try:
                story_priority = StoryPriority(priority.lower())
            except ValueError:
                raise ValueError(f"Invalid priority '{priority}'. Must be: low, medium, high")
        
        # Update entity
        entity.update_details(
            title=title,
            description=description,
            status=story_status,
            priority=story_priority,
            points=points,
        )
        
        # Save to repository
        saved_entity = await self._repository.save(entity)
        
        if not saved_entity:
            raise ValueError("Failed to update story")
        
        # Return DTO using shared mapper
        return to_story_response(saved_entity)