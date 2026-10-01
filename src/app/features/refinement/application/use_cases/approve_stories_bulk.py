"""Approve several refined stories at once."""

from uuid import UUID

from src.app.features.projects.domain.repositories.project_repository import ProjectRepository
from src.app.features.refinement.application.dtos.refinement_dto import ApproveStoriesBulkRequest
from src.app.features.refinement.application.mappers.approved_story_to_entity import approved_story_to_entity
from src.app.features.stories.application.dtos.story_dto import StoryResponse
from src.app.features.stories.application.mappers.story_mapper import to_story_response
from src.app.features.stories.domain.repositories.story_repository import StoryRepository
from src.app.shared.application.request_context import RequestContext
from src.app.shared.domain.exceptions.domain_exceptions import NotFoundError
from src.app.shared.domain.value_objects.entity_id import EntityId
from src.app.shared.logging import get_logger, set_user_id


class ApproveStoriesBulkUseCase:
    """Use case for approving several refined stories and saving them to the backlog."""

    def __init__(self, story_repository: StoryRepository, project_repository: ProjectRepository):
        """
        Initialize use case.

        Args:
            story_repository: Story repository
            project_repository: Confirms every target project is in the caller's workspace
        """
        self._story_repository = story_repository
        self._project_repository = project_repository

    async def execute(self, request: ApproveStoriesBulkRequest, ctx: RequestContext) -> list[StoryResponse]:
        """
        Execute bulk approve use case.

        Every project is checked and every story built before the first save, so a foreign
        project or an invalid story rejects the whole batch instead of saving part of it.

        Args:
            request: The refined stories the Admin approved
            ctx: Caller identity and workspace

        Returns:
            StoryResponse for each created story

        Raises:
            NotFoundError: If any project is not in the caller's workspace
            ValidationError: If any story content is invalid
        """
        log = get_logger(__name__)
        set_user_id(str(ctx.user_id))

        for project_id in {story.project_id for story in request.stories}:
            project_uuid = EntityId.from_string(project_id)
            if not await self._project_repository.exists(project_uuid.value, workspace_id=ctx.workspace_id.value):
                raise NotFoundError("Project", project_id)

        entities = [approved_story_to_entity(story, ctx.user_id) for story in request.stories]

        created_stories: list[StoryResponse] = []
        try:
            for entity in entities:
                story = await self._story_repository.save(entity)
                if not story:
                    raise ValueError("Failed to create story from approved refinement")
                created_stories.append(to_story_response(story))
        except Exception:
            # Each save commits on its own, and the client keeps the batch on failure so the
            # Admin can retry; stories left behind would be duplicated by that retry.
            for created in created_stories:
                await self._story_repository.delete(UUID(str(created.id)), workspace_id=ctx.workspace_id.value)
            raise

        log.info(
            "Bulk approval completed",
            extra={
                "event_type": "refinement.bulk_approve.completed",
                "approved_count": len(created_stories),
            },
        )

        return created_stories
