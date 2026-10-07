"""Get story by ID use case."""

from uuid import UUID

from src.app.features.stories.application.dtos.story_dto import StoryResponse
from src.app.features.stories.application.mappers.story_mapper import to_story_response
from src.app.features.stories.domain.exceptions.story_exceptions import StoryNotFoundError
from src.app.features.stories.domain.repositories.story_repository import StoryRepository
from src.app.shared.application.request_context import RequestContext
from src.app.shared.logging import get_logger, set_user_id


class GetStoryByIdUseCase:
    """Use case for getting a story by ID."""

    def __init__(self, story_repository: StoryRepository):
        """
        Initialize use case.

        Args:
            story_repository: Story repository
        """
        self._repository = story_repository

    async def execute(self, story_id: str, ctx: RequestContext) -> StoryResponse:
        """
        Execute get story by ID use case.

        Args:
            story_id: Story UUID
            ctx: Caller identity and workspace

        Returns:
            StoryResponse with story data

        Raises:
            StoryNotFoundError: If story not found
        """
        log = get_logger(__name__)
        set_user_id(str(ctx.user_id))
        log.info(
            "Fetching story by ID",
            extra={"event_type": "stories.fetch_by_id.started", "story_id": story_id},
        )

        entity = await self._repository.find_by_id(UUID(story_id), workspace_id=ctx.workspace_id.value)

        if not entity:
            log.warning(
                "Story not found",
                extra={"event_type": "stories.fetch_by_id.not_found", "story_id": story_id},
            )
            raise StoryNotFoundError(story_id)

        log.info(
            "Story fetched by ID successfully",
            extra={"event_type": "stories.fetch_by_id.success", "story_id": story_id},
        )
        return to_story_response(entity)
