"""Assign story use case."""

from uuid import UUID

from src.app.features.stories.application.dtos.story_dto import StoryResponse
from src.app.features.stories.application.mappers.story_mapper import to_story_response
from src.app.features.stories.domain.repositories.story_repository import StoryRepository
from src.app.shared.domain.value_objects.entity_id import EntityId
from src.app.shared.logging import get_logger, log_business_event, log_error_event


log = get_logger(__name__)


class AssignStoryUseCase:
    """Use case for assigning a story to a user."""

    def __init__(self, story_repository: StoryRepository):
        """
        Initialize use case.

        Args:
            story_repository: Story repository
        """
        self._repository = story_repository

    async def execute(self, story_id: str, user_id: str) -> StoryResponse | None:
        """
        Execute assign story use case.

        Args:
            story_id: Story UUID
            user_id: User UUID to assign

        Returns:
            StoryResponse if found and assigned, None otherwise

        Raises:
            ValueError: If validation fails
        """
        try:
            entity = await self._repository.find_by_id(UUID(story_id))

            if not entity:
                log.warning(
                    "Story not found for assignment",
                    extra={
                        "story_id": story_id,
                        "user_id": user_id,
                        "event_type": "story.assign.not_found",
                    },
                )
                return None

            # Track previous assignment for logging
            previous_assignee = str(entity.assigned_to) if entity.assigned_to else None

            entity.assign_to(EntityId.from_string(user_id))

            saved_entity = await self._repository.save(entity)

            if not saved_entity:
                log_error_event(
                    logger=log,
                    error_type="story.assign.save_failed",
                    message="Failed to save story assignment",
                    entity_id=story_id,
                    additional_data={"assigned_to": user_id},
                )
                raise ValueError("Failed to assign story")

            log_business_event(
                logger=log,
                event_type="story.assigned",
                message="Story assigned successfully",
                entity_id=story_id,
                additional_data={
                    "story_title": saved_entity.title,
                    "assigned_to": user_id,
                    "previous_assignee": previous_assignee,
                },
            )

            return to_story_response(saved_entity)

        except ValueError:
            raise
        except Exception as e:
            log_error_event(
                logger=log,
                error_type="story.assign.unexpected_error",
                message="Unexpected error during story assignment",
                error=e,
                entity_id=story_id,
            )
            raise
