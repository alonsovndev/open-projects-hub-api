"""Approve story use case - save an approved refined story to the backlog."""

from src.app.features.projects.domain.repositories.project_repository import ProjectRepository
from src.app.features.refinement.application.dtos.refinement_dto import ApproveStoryRequest
from src.app.features.refinement.application.mappers.approved_story_to_entity import approved_story_to_entity
from src.app.features.stories.application.dtos.story_dto import StoryResponse
from src.app.features.stories.application.mappers.story_mapper import to_story_response
from src.app.features.stories.domain.repositories.story_repository import StoryRepository
from src.app.shared.application.request_context import RequestContext
from src.app.shared.domain.exceptions.domain_exceptions import NotFoundError
from src.app.shared.domain.value_objects.entity_id import EntityId
from src.app.shared.logging import get_logger, set_user_id


class ApproveStoryUseCase:
    """Use case for approving one refined story; it is persisted only at this point."""

    def __init__(self, story_repository: StoryRepository, project_repository: ProjectRepository):
        """
        Initialize use case.

        Args:
            story_repository: Story repository
            project_repository: Confirms the target project is in the caller's workspace
        """
        self._story_repository = story_repository
        self._project_repository = project_repository

    async def execute(self, request: ApproveStoryRequest, ctx: RequestContext) -> StoryResponse:
        """
        Execute approve story use case.

        Args:
            request: The refined story content the Admin approved
            ctx: Caller identity and workspace

        Returns:
            StoryResponse with created story data

        Raises:
            NotFoundError: If the project is not in the caller's workspace
            ValidationError: If the story content is invalid
        """
        log = get_logger(__name__)
        set_user_id(str(ctx.user_id))

        project_id = EntityId.from_string(request.project_id)
        if not await self._project_repository.exists(project_id.value, workspace_id=ctx.workspace_id.value):
            raise NotFoundError("Project", request.project_id)

        story = await self._story_repository.save(approved_story_to_entity(request, ctx.user_id))

        if not story:
            raise ValueError("Failed to create story from approved refinement")

        log.info(
            "Refined story approved and saved",
            extra={
                "event_type": "refinement.story.approved",
                "story_id": str(story.id.value),
                "project_id": request.project_id,
                "story_title": story.title,
            },
        )

        return to_story_response(story)
