"""List stories use case."""

from uuid import UUID

from src.app.features.stories.application.dtos.story_dto import StoryResponse
from src.app.features.stories.application.mappers.story_mapper import to_story_response
from src.app.features.stories.domain.repositories.story_repository import StoryRepository
from src.app.features.stories.domain.value_objects.story_priority import StoryPriority
from src.app.features.stories.domain.value_objects.story_status import StoryStatus
from src.app.shared.application.dtos.pagination_dto import PaginatedResponse
from src.app.shared.application.request_context import RequestContext
from src.app.shared.domain.exceptions.domain_exceptions import ValidationError
from src.app.shared.logging import get_logger, set_user_id


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
        ctx: RequestContext,
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
            ctx: Caller identity and workspace
            limit: Maximum number of results (default 20)
            offset: Number of results to skip (default 0)
            project_id: Optional project filter
            status: Optional status filter (todo, in_progress, done)
            priority: Optional priority filter (low, medium, high)
            assigned_to: Optional assigned user filter

        Returns:
            PaginatedResponse containing pagination metadata and StoryResponse items

        Raises:
            ValidationError: If validation fails
        """
        # Validate status enum early to provide clear user feedback
        if status and status not in [s.value for s in StoryStatus]:
            raise ValidationError(f"Status must be one of: {', '.join(s.value for s in StoryStatus)}")

        # Validate priority enum early to provide clear user feedback
        if priority and priority not in [p.value for p in StoryPriority]:
            raise ValidationError(f"Priority must be one of: {', '.join(p.value for p in StoryPriority)}")

        log = get_logger(__name__)
        set_user_id(str(ctx.user_id))
        log.info(
            "Listing stories",
            extra={
                "event_type": "stories.list.started",
                "limit": limit,
                "offset": offset,
                "project_id": project_id,
                "status": status,
                "priority": priority,
                "assigned_to": assigned_to,
            },
        )

        project_uuid = UUID(project_id) if project_id else None
        assigned_to_uuid = UUID(assigned_to) if assigned_to else None

        total = await self._repository.count(
            workspace_id=ctx.workspace_id.value,
            project_id=project_uuid,
            status=status,
            priority=priority,
            assigned_to=assigned_to_uuid,
        )
        entities = await self._repository.find_all(
            workspace_id=ctx.workspace_id.value,
            limit=limit,
            offset=offset,
            project_id=project_uuid,
            status=status,
            priority=priority,
            assigned_to=assigned_to_uuid,
        )

        items = [to_story_response(e) for e in entities]

        page = (offset // limit) + 1 if limit > 0 else 1

        log.info(
            "Stories listed successfully",
            extra={"event_type": "stories.list.success", "total": total, "returned": len(items)},
        )
        return PaginatedResponse(
            total=total,
            page=page,
            per_page=limit,
            items=items,
        )
