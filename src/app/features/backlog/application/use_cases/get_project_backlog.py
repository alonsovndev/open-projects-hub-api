"""GetProjectBacklogUseCase - the approved backlog as a structured, reviewable list."""

from uuid import UUID

from src.app.features.backlog.application.dtos.backlog_dto import BacklogStoryResponse
from src.app.features.backlog.application.mappers.backlog_mapper import to_backlog_story_response
from src.app.features.projects.domain.exceptions.project_exceptions import ProjectNotFoundError
from src.app.features.projects.domain.repositories.project_repository import ProjectRepository
from src.app.features.stories.domain.queries.backlog_query import BacklogQuery
from src.app.features.stories.domain.repositories.story_repository import StoryRepository
from src.app.shared.application.dtos.pagination_dto import PaginatedResponse
from src.app.shared.application.request_context import RequestContext
from src.app.shared.logging import get_logger


class GetProjectBacklogUseCase:
    """
    Returns a project's approved backlog with acceptance criteria.

    Drafts are excluded structurally rather than by a filter: unapproved work lives in
    story_drafts and never reaches this table.
    """

    def __init__(self, story_repository: StoryRepository, project_repository: ProjectRepository):
        self._story_repository = story_repository
        self._project_repository = project_repository

    async def execute(
        self, project_id: UUID, ctx: RequestContext, limit: int = 50, offset: int = 0
    ) -> PaginatedResponse[BacklogStoryResponse]:
        """
        Fetch a page of the project's backlog.

        Args:
            project_id: The project to read
            ctx: Caller identity and workspace
            limit: Maximum number of stories to return
            offset: Number of stories to skip

        Returns:
            Paginated backlog stories in priority-then-age order

        Raises:
            ProjectNotFoundError: If the project is not in the caller's workspace
        """
        log = get_logger(__name__)
        log.info(
            "Fetching project backlog", extra={"event_type": "backlog.fetch.started", "project_id": str(project_id)}
        )

        workspace_id = ctx.workspace_id.value
        if await self._project_repository.find_by_id(project_id, workspace_id=workspace_id) is None:
            raise ProjectNotFoundError(str(project_id))

        query = BacklogQuery(project_id=project_id, workspace_id=workspace_id, limit=limit, offset=offset)

        total = await self._story_repository.count_backlog(query)
        stories = await self._story_repository.find_backlog(query)

        log.info(
            "Project backlog fetched",
            extra={"event_type": "backlog.fetch.success", "project_id": str(project_id), "total": total},
        )

        return PaginatedResponse[BacklogStoryResponse](
            total=total,
            page=(offset // limit) + 1,
            per_page=limit,
            items=[to_backlog_story_response(story) for story in stories],
        )
