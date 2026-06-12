"""Assign story use case."""

from uuid import UUID

from src.app.features.stories.application.dtos.story_dto import StoryResponse
from src.app.features.stories.application.mappers.story_mapper import to_story_response
from src.app.features.stories.domain.exceptions.story_exceptions import StoryNotFoundError
from src.app.features.stories.domain.repositories.story_repository import StoryRepository
from src.app.shared.domain.value_objects.entity_id import EntityId
from src.app.shared.logging import BusinessLogger, get_logger


class AssignStoryUseCase:
    """Use case for assigning a story to a user."""

    def __init__(self, story_repository: StoryRepository):
        """
        Initialize use case.

        Args:
            story_repository: Story repository
        """
        self._repository = story_repository

    async def execute(self, story_id: str, user_id: str, created_by: str) -> StoryResponse:
        """
        Execute assign story use case.

        Args:
            story_id: Story UUID
            user_id: User UUID to assign
            created_by: User ID performing the assignment

        Returns:
            StoryResponse with updated story data

        Raises:
            StoryNotFoundError: If story not found
        """
        log = BusinessLogger(get_logger(__name__), user_id=created_by)

        entity = await self._repository.find_by_id(UUID(story_id))

        if not entity:
            log.failure("story.assign.not_found", entity_id=story_id, assigned_to=user_id)
            raise StoryNotFoundError(story_id)

        # Track previous assignment for logging
        previous_assignee = str(entity.assigned_to) if entity.assigned_to else None

        entity.assign_to(EntityId.from_string(user_id))

        saved_entity = await self._repository.save(entity)

        if not saved_entity:
            log.failure("story.assign.save_failed", assigned_to=user_id)
            raise RuntimeError("Failed to assign story")

        log.event(
            "story.assigned",
            entity_id=story_id,
            story_title=saved_entity.title,
            assigned_to=user_id,
            previous_assignee=previous_assignee,
        )

        return to_story_response(saved_entity)
