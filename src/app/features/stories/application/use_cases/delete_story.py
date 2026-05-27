"""Delete story use case."""

from uuid import UUID

from src.app.features.stories.domain.repositories.story_repository import StoryRepository
from src.app.shared.logging import get_logger, log_business_event, log_error_event


log = get_logger(__name__)


class DeleteStoryUseCase:
    """Use case for deleting a story."""

    def __init__(self, story_repository: StoryRepository):
        """
        Initialize use case.

        Args:
            story_repository: Story repository
        """
        self._repository = story_repository

    async def execute(self, story_id: str) -> bool:
        """
        Execute delete story use case.

        Args:
            story_id: Story UUID

        Returns:
            True if deleted, False if not found
        """
        try:
            # Get story details before deletion for logging
            entity = await self._repository.find_by_id(UUID(story_id))
            if not entity:
                log.warning(
                    "Story not found for deletion",
                    extra={
                        "story_id": story_id,
                        "event_type": "story.delete.not_found",
                    },
                )
                return False

            story_title = entity.title
            project_id = str(entity.project_id)

            deleted = await self._repository.delete(UUID(story_id))

            if deleted:
                log_business_event(
                    logger=log,
                    event_type="story.deleted",
                    message="Story deleted successfully",
                    entity_id=story_id,
                    additional_data={
                        "story_title": story_title,
                        "project_id": project_id,
                    },
                )
            else:
                log_error_event(
                    logger=log,
                    error_type="story.delete.failed",
                    message="Failed to delete story from repository",
                    entity_id=story_id,
                )

            return deleted

        except Exception as e:
            log_error_event(
                logger=log,
                error_type="story.delete.unexpected_error",
                message="Unexpected error during story deletion",
                error=e,
                entity_id=story_id,
            )
            raise
