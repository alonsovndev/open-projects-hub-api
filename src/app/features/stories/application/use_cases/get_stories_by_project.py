"""Get stories by project use case."""

from uuid import UUID

from src.app.features.stories.application.dtos.story_dto import StoryResponse
from src.app.features.stories.application.mappers.story_mapper import to_story_response
from src.app.features.stories.domain.repositories.story_repository import StoryRepository
from src.app.shared.application.dtos.pagination_dto import PaginatedResponse
from src.app.shared.logging import get_logger, set_user_id


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
        user_id: str,
        limit: int = 20,
        offset: int = 0,
    ) -> PaginatedResponse[StoryResponse]:
        """
        Execute get stories by project use case.

        Args:
            project_id: Project UUID
            user_id: Current user ID
            limit: Maximum number of results (default 20)
            offset: Number of results to skip (default 0)

        Returns:
            PaginatedResponse containing pagination metadata and StoryResponse items
        """
        log = get_logger(__name__)
        set_user_id(user_id)
        log.info(
            "Fetching stories by project",
            extra={
                "event_type": "stories.fetch_by_project.started",
                "project_id": project_id,
                "limit": limit,
                "offset": offset,
            },
        )

        project_uuid = UUID(project_id)

        total = await self._repository.count(project_id=project_uuid)
        entities = await self._repository.find_by_project_id(
            project_id=project_uuid,
            limit=limit,
            offset=offset,
        )

        items = [to_story_response(e) for e in entities]

        page = (offset // limit) + 1 if limit > 0 else 1

        log.info(
            "Stories fetched by project successfully",
            extra={
                "event_type": "stories.fetch_by_project.success",
                "project_id": project_id,
                "total": total,
                "returned": len(items),
            },
        )
        return PaginatedResponse(
            total=total,
            page=page,
            per_page=limit,
            items=items,
        )
