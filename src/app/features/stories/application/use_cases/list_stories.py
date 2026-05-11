"""List stories use case."""
from typing import List, Optional

from src.app.features.stories.application.dtos.story_dto import StoryResponse
from src.app.features.stories.domain.repositories.story_repository import StoryRepository
from src.app.shared.infrastructure.mappers.story_mapper import to_story_response


class ListStoriesUseCase:
    """Use case for listing stories with filters."""
    
    def __init__(self, story_repository: StoryRepository):
        """
        Initialize use case.
        
        Args:
            story_repository: Story repository
        """
        self._repository = story_repository
    
    async def execute(
        self,
        limit: int = 20,
        offset: int = 0,
        project_id: Optional[str] = None,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        assigned_to: Optional[str] = None,
    ) -> List[StoryResponse]:
        """
        Execute list stories use case.
        
        Args:
            limit: Maximum number of results (default 20)
            offset: Number of results to skip (default 0)
            project_id: Optional project filter
            status: Optional status filter (todo, in_progress, done)
            priority: Optional priority filter (low, medium, high)
            assigned_to: Optional assigned user filter
            
        Returns:
            List of StoryResponse objects
            
        Raises:
            ValueError: If validation fails
        """
        # Validate status
        if status and status not in ["todo", "in_progress", "done"]:
            raise ValueError("Status must be one of: todo, in_progress, done")
        
        # Validate priority
        if priority and priority not in ["low", "medium", "high"]:
            raise ValueError("Priority must be one of: low, medium, high")
        
        # Get entities from repository
        entities = await self._repository.find_all(
            limit=limit,
            offset=offset,
            project_id=self._to_uuid(project_id) if project_id else None,
            status=status,
            priority=priority,
            assigned_to=self._to_uuid(assigned_to) if assigned_to else None,
        )
        
        # Convert to DTOs using shared mapper
        return [to_story_response(e) for e in entities]
    
    @staticmethod
    def _to_uuid(value: str):
        """Convert string to UUID."""
        from uuid import UUID
        return UUID(value)