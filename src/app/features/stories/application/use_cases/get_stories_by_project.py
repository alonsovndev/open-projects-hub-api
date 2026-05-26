"""Get stories by project use case."""

from uuid import UUID

from src.app.features.stories.application.dtos.story_dto import StoryResponse
from src.app.features.stories.application.mappers.story_mapper import to_story_response
from src.app.features.stories.domain.repositories.story_repository import StoryRepository
from src.app.shared.application.dtos.pagination_dto import PaginatedResponse


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
    ) -> PaginatedResponse[StoryResponse]:
        """
        Execute get stories by project use case.

        Args:
            project_id: Project UUID
            limit: Maximum number of results (default 20)
            offset: Number of results to skip (default 0)

        Returns:
            PaginatedResponse containing pagination metadata and StoryResponse items
        """
        project_uuid = UUID(project_id)

        total = await self._repository.count(project_id=project_uuid)
        entities = await self._repository.find_by_project_id(
            project_id=project_uuid,
            limit=limit,
            offset=offset,
        )

        items = [to_story_response(e) for e in entities]

        # Calculate page number (1-indexed)
        page = (offset // limit) + 1 if limit > 0 else 1

        return PaginatedResponse(
            total=total,
            page=page,
            per_page=limit,
            items=items,
        )
