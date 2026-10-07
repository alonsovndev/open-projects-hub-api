"""Update story use case."""

from uuid import UUID

from src.app.features.stories.application.dtos.story_dto import StoryResponse, UpdateStoryRequest
from src.app.features.stories.application.mappers.story_mapper import to_story_response
from src.app.features.stories.domain.exceptions.story_exceptions import StoryNotFoundError
from src.app.features.stories.domain.repositories.story_repository import StoryRepository
from src.app.features.stories.domain.value_objects.story_priority import StoryPriority
from src.app.features.stories.domain.value_objects.story_status import StoryStatus
from src.app.shared.application.request_context import RequestContext
from src.app.shared.logging import get_logger, set_user_id


class UpdateStoryUseCase:
    """Use case for updating a story."""

    def __init__(self, story_repository: StoryRepository):
        """
        Initialize use case.

        Args:
            story_repository: Story repository
        """
        self._repository = story_repository

    async def execute(self, story_id: str, request: UpdateStoryRequest, ctx: RequestContext) -> StoryResponse:
        """
        Execute update story use case.

        Args:
            story_id: Story UUID
            request: UpdateStoryRequest DTO with fields to update
            ctx: Caller identity and workspace

        Returns:
            StoryResponse with updated story data

        Raises:
            StoryNotFoundError: If story not found
        """
        log = get_logger(__name__)
        set_user_id(str(ctx.user_id))

        entity = await self._repository.find_by_id(UUID(story_id), workspace_id=ctx.workspace_id.value)

        if not entity:
            log.error(
                "Story not found for update",
                extra={"event_type": "story.update.not_found", "entity_id": story_id},
            )
            raise StoryNotFoundError(story_id)

        # Track changes for logging
        changes = {}
        if request.title and request.title != entity.title:
            changes["title"] = {"old": entity.title, "new": request.title}
        if request.status and request.status != entity.status.value:
            changes["status"] = {"old": entity.status.value, "new": request.status}
        if request.priority and request.priority != (entity.priority.value if entity.priority else None):
            changes["priority"] = {
                "old": entity.priority.value if entity.priority else None,
                "new": request.priority,
            }

        story_status = StoryStatus(request.status) if request.status else None
        story_priority = StoryPriority(request.priority) if request.priority else None

        entity.update_details(
            title=request.title,
            description=request.description,
            status=story_status,
            priority=story_priority,
            points=request.points,
            acceptance_criteria=request.acceptance_criteria,
        )

        saved_entity = await self._repository.save(entity)

        if not saved_entity:
            log.error(
                "Failed to save story update",
                extra={"event_type": "story.update.save_failed", "entity_id": story_id},
            )
            raise RuntimeError("Failed to update story")

        log.info(
            "Story updated",
            extra={
                "event_type": "story.updated",
                "entity_id": story_id,
                "story_title": saved_entity.title,
                "changes": changes,
            },
        )

        return to_story_response(saved_entity)
