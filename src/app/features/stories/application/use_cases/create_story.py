"""Create story use case."""
from typing import Optional

from src.app.features.stories.application.dtos.story_dto import StoryResponse
from src.app.features.stories.domain.entities.story_entity import StoryEntity
from src.app.features.stories.domain.repositories.story_repository import StoryRepository
from src.app.features.stories.domain.value_objects.story_priority import StoryPriority
from src.app.shared.domain.value_objects.entity_id import EntityId
from src.app.shared.infrastructure.mappers.story_mapper import to_story_response


class CreateStoryUseCase:
    """Use case for creating a new story."""
    
    def __init__(self, story_repository: StoryRepository):
        """
        Initialize use case.
        
        Args:
            story_repository: Story repository
        """
        self._repository = story_repository
    
    async def execute(
        self,
        title: str,
        project_id: str,
        created_by: str,
        description: Optional[str] = None,
        priority: Optional[str] = None,
        points: Optional[int] = None,
    ) -> StoryResponse:
        """
        Execute create story use case.
        
        Args:
            title: Story title
            project_id: Parent project ID
            created_by: User ID of creator
            description: Optional description
            priority: Optional priority (low, medium, high)
            points: Optional story points
            
        Returns:
            StoryResponse with created story data
            
        Raises:
            ValueError: If validation fails
        """
        # Validate priority
        story_priority = None
        if priority:
            try:
                story_priority = StoryPriority(priority.lower())
            except ValueError:
                raise ValueError(f"Invalid priority '{priority}'. Must be: low, medium, high")
        
        # Create entity
        entity = StoryEntity.create(
            title=title,
            project_id=EntityId.from_string(project_id),
            created_by=EntityId.from_string(created_by),
            description=description,
            priority=story_priority,
            points=points,
        )
        
        # Save to repository
        saved_entity = await self._repository.save(entity)
        
        if not saved_entity:
            raise ValueError("Failed to create story")
        
        # Return DTO using shared mapper
        return to_story_response(saved_entity)