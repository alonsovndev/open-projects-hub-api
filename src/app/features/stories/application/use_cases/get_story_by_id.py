"""Get story by ID use case."""

from src.app.features.stories.application.dtos.story_dto import StoryResponse
from src.app.features.stories.application.mappers.story_mapper import to_story_response
from src.app.features.stories.domain.repositories.story_repository import StoryRepository


class GetStoryByIdUseCase:
    """Use case for getting a story by ID."""

    def __init__(self, story_repository: StoryRepository):
        """
        Initialize use case.

        Args:
            story_repository: Story repository
        """
        self._repository = story_repository

    async def execute(self, story_id: str) -> StoryResponse | None:
        """
        Execute get story by ID use case.

        Args:
            story_id: Story UUID

        Returns:
            StoryResponse if found, None otherwise
        """
        from uuid import UUID

        entity = await self._repository.find_by_id(UUID(story_id))

        if not entity:
            return None

        return to_story_response(entity)
