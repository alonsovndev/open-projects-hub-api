"""GetClientReviewUseCase - the approved stories a client stakeholder opens with an access code."""

from src.app.features.backlog.application.mappers.backlog_mapper import to_backlog_story_response
from src.app.features.client_review.application.dtos.client_review_dto import ClientReviewResponse
from src.app.features.projects.domain.exceptions.project_exceptions import ProjectNotFoundError
from src.app.features.projects.domain.repositories.project_repository import ProjectRepository
from src.app.features.projects.domain.value_objects.access_code import is_valid_access_code, normalize_access_code
from src.app.features.stories.domain.queries.backlog_query import BacklogQuery
from src.app.features.stories.domain.repositories.story_repository import StoryRepository
from src.app.shared.logging import get_logger


class GetClientReviewUseCase:
    """
    Resolves an access code to its project and returns the approved backlog.

    The caller has no session, so the workspace comes from the project the code resolves to,
    never from the request. A malformed, unknown or mistyped code all raise the same
    ProjectNotFoundError so the response does not tell a guesser how close they were.
    """

    def __init__(self, story_repository: StoryRepository, project_repository: ProjectRepository):
        self._story_repository = story_repository
        self._project_repository = project_repository

    async def execute(self, access_code: str, limit: int = 100, offset: int = 0) -> ClientReviewResponse:
        """
        Fetch the project's approved stories.

        Args:
            access_code: Code as typed by the stakeholder
            limit: Maximum number of stories to return
            offset: Number of stories to skip

        Returns:
            The project name, phase and a page of approved stories in priority-then-age order

        Raises:
            ProjectNotFoundError: If no project has this access code
        """
        log = get_logger(__name__)
        normalized_code = normalize_access_code(access_code)

        project = None
        # The format check spares the database a lookup for input that can never match.
        if is_valid_access_code(normalized_code):
            project = await self._project_repository.find_by_access_code(normalized_code)
        if project is None or project.workspace_id is None:
            log.info("Client review not found", extra={"event_type": "client_review.not_found"})
            raise ProjectNotFoundError("access code")

        query = BacklogQuery(
            project_id=project.id.value, workspace_id=project.workspace_id.value, limit=limit, offset=offset
        )
        total = await self._story_repository.count_backlog(query)
        stories = await self._story_repository.find_backlog(query)

        log.info(
            "Client review opened",
            extra={"event_type": "client_review.opened", "project_id": str(project.id.value), "total": total},
        )

        return ClientReviewResponse(
            project_name=project.name,
            phase=project.phase.value,
            total=total,
            stories=[to_backlog_story_response(story) for story in stories],
        )
