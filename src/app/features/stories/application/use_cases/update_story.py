"""Update story use case."""

from uuid import UUID

from src.app.features.stories.application.dtos.story_dto import StoryResponse, UpdateStoryRequest
from src.app.features.stories.application.mappers.story_mapper import to_story_response
from src.app.features.stories.domain.repositories.story_repository import StoryRepository
from src.app.features.stories.domain.value_objects.story_priority import StoryPriority
from src.app.features.stories.domain.value_objects.story_status import StoryStatus


class UpdateStoryUseCase:
    """Use case for updating a story."""

    def __init__(self, story_repository: StoryRepository):
        """
        Initialize use case.

        Args:
            story_repository: Story repository
        """
        self._repository = story_repository

    async def execute(self, story_id: str, request: UpdateStoryRequest) -> StoryResponse | None:
        """
        Execute update story use case.

        Args:
            story_id: Story UUID
            request: UpdateStoryRequest DTO with fields to update

        Returns:
            StoryResponse if found and updated, None otherwise

        Raises:
            ValueError: If validation fails
        """
        entity = await self._repository.find_by_id(UUID(story_id))

        if not entity:
            return None

        # Validate status enum early to provide clear user feedback
        story_status = None
        if request.status:
            try:
                story_status = StoryStatus(request.status.lower())
            except ValueError:
                raise ValueError(f"Invalid status '{request.status}'. Must be: todo, in_progress, done")

        # Validate priority enum early to provide clear user feedback
        story_priority = None
        if request.priority:
            try:
                story_priority = StoryPriority(request.priority.lower())
            except ValueError:
                raise ValueError(f"Invalid priority '{request.priority}'. Must be: low, medium, high")

        entity.update_details(
            title=request.title,
            description=request.description,
            status=story_status,
            priority=story_priority,
            points=request.points,
        )

        saved_entity = await self._repository.save(entity)

        if not saved_entity:
            raise ValueError("Failed to update story")

        return to_story_response(saved_entity)
