"""Get story by ID use case."""

from uuid import UUID

from src.app.features.stories.application.dtos.story_dto import StoryResponse
from src.app.features.stories.application.mappers.story_mapper import to_story_response
from src.app.features.stories.domain.exceptions.story_exceptions import StoryNotFoundError
from src.app.features.stories.domain.repositories.story_repository import StoryRepository
from src.app.shared.logging import BusinessLogger, get_logger


class GetStoryByIdUseCase:
    """Use case for getting a story by ID."""

    def __init__(self, story_repository: StoryRepository):
        """
        Initialize use case.

        Args:
            story_repository: Story repository
        """
        self._repository = story_repository

    async def execute(self, story_id: str, user_id: str) -> StoryResponse:
        """
        Execute get story by ID use case.

        Args:
            story_id: Story UUID
            user_id: Current user ID

        Returns:
            StoryResponse with story data

        Raises:
            StoryNotFoundError: If story not found
        """
        log = BusinessLogger(get_logger(__name__), user_id=user_id)
        log.info("Fetching story by ID", event_type="stories.fetch_by_id.started", story_id=story_id)

        entity = await self._repository.find_by_id(UUID(story_id))

        if not entity:
            log.warning("Story not found", event_type="stories.fetch_by_id.not_found", story_id=story_id)
            raise StoryNotFoundError(story_id)

        log.event("stories.fetch_by_id.success", story_id=story_id)
        return to_story_response(entity)
