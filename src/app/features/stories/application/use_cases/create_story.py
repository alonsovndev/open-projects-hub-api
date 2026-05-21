"""Create story use case."""
from src.app.features.stories.application.dtos.story_dto import (
    CreateStoryRequest,
    StoryResponse,
)
from src.app.features.stories.domain.entities.story_entity import StoryEntity
from src.app.features.stories.domain.repositories.story_repository import StoryRepository
from src.app.features.stories.domain.value_objects.story_priority import StoryPriority
from src.app.shared.domain.value_objects.entity_id import EntityId
from src.app.features.stories.application.mappers.story_mapper import to_story_response


class CreateStoryUseCase:
    """Use case for creating a new story."""
    
    def __init__(self, story_repository: StoryRepository):
        """
        Initialize use case.
        
        Args:
            story_repository: Story repository
        """
        self._repository = story_repository
    
    async def execute(self, request: CreateStoryRequest, created_by: str) -> StoryResponse:
        """
        Execute create story use case.
        
        Args:
            request: CreateStoryRequest DTO with story data
            created_by: User ID of creator (from JWT token)
            
        Returns:
            StoryResponse with created story data
            
        Raises:
            ValueError: If validation fails
        """
        # Validate priority enum early to provide clear user feedback
        story_priority = None
        if request.priority:
            try:
                story_priority = StoryPriority(request.priority.lower())
            except ValueError:
                raise ValueError(f"Invalid priority '{request.priority}'. Must be: low, medium, high")
        
        entity = StoryEntity.create(
            title=request.title,
            project_id=EntityId.from_string(request.project_id),
            created_by=EntityId.from_string(created_by),
            description=request.description,
            priority=story_priority,
            points=request.points,
        )
        
        saved_entity = await self._repository.save(entity)
        
        if not saved_entity:
            raise ValueError("Failed to create story")
        
        return to_story_response(saved_entity)