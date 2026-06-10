"""List stories use case."""

from uuid import UUID

from src.app.features.stories.application.dtos.story_dto import StoryResponse
from src.app.features.stories.application.mappers.story_mapper import to_story_response
from src.app.features.stories.domain.repositories.story_repository import StoryRepository
from src.app.shared.application.dtos.pagination_dto import PaginatedResponse
from src.app.shared.logging import BusinessLogger, get_logger


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
        user_id: str,
        limit: int = 20,
        offset: int = 0,
        project_id: str | None = None,
        status: str | None = None,
        priority: str | None = None,
        assigned_to: str | None = None,
    ) -> PaginatedResponse[StoryResponse]:
        """
        Execute list stories use case.

        Args:
            user_id: Current user ID
            limit: Maximum number of results (default 20)
            offset: Number of results to skip (default 0)
            project_id: Optional project filter
            status: Optional status filter (todo, in_progress, done)
            priority: Optional priority filter (low, medium, high)
            assigned_to: Optional assigned user filter

        Returns:
            PaginatedResponse containing pagination metadata and StoryResponse items

        Raises:
            ValueError: If validation fails
        """
        # Validate status enum early to provide clear user feedback
        if status and status not in ["todo", "in_progress", "done"]:
            raise ValueError("Status must be one of: todo, in_progress, done")

        # Validate priority enum early to provide clear user feedback
        if priority and priority not in ["low", "medium", "high"]:
            raise ValueError("Priority must be one of: low, medium, high")

        log = BusinessLogger(get_logger(__name__), user_id=user_id)
        log.info(
            "Listing stories",
            event_type="stories.list.started",
            limit=limit,
            offset=offset,
            project_id=project_id,
            status=status,
            priority=priority,
            assigned_to=assigned_to,
        )

        project_uuid = UUID(project_id) if project_id else None
        assigned_to_uuid = UUID(assigned_to) if assigned_to else None

        total = await self._repository.count(
            project_id=project_uuid,
            status=status,
            priority=priority,
            assigned_to=assigned_to_uuid,
        )
        entities = await self._repository.find_all(
            limit=limit,
            offset=offset,
            project_id=project_uuid,
            status=status,
            priority=priority,
            assigned_to=assigned_to_uuid,
        )

        items = [to_story_response(e) for e in entities]

        page = (offset // limit) + 1 if limit > 0 else 1

        log.event("stories.list.success", total=total, returned=len(items))
        return PaginatedResponse(
            total=total,
            page=page,
            per_page=limit,
            items=items,
        )
