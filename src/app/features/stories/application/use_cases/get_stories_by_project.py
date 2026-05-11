"""Get stories by project use case."""
from typing import List
from uuid import UUID

from src.app.features.stories.application.dtos.story_dto import StoryResponse
from src.app.features.stories.domain.repositories.story_repository import StoryRepository
from src.app.shared.infrastructure.mappers.story_mapper import to_story_response


class GetStoriesByProjectUseCase:
    """Use case for getting stories by project ID."""
    
    def __init__(self, story_repository: StoryRepository):
        """
        Initialize use case.
        
        Args:
            story_repository: Story repository
        """
        self._repository = story_repository
    
    async def execute(
        self,
        project_id: str,
        limit: int = 20,
        offset: int = 0,
    ) -> List[StoryResponse]:
        """
        Execute get stories by project use case.
        
        Args:
            project_id: Project UUID
            limit: Maximum number of results (default 20)
            offset: Number of results to skip (default 0)
            
        Returns:
            List of StoryResponse objects
        """
        entities = await self._repository.find_by_project_id(
            project_id=UUID(project_id),
            limit=limit,
            offset=offset,
        )
        
        # Convert to DTOs using shared mapper
        return [to_story_response(e) for e in entities]