"""Delete story use case."""

from uuid import UUID

from src.app.features.stories.domain.repositories.story_repository import StoryRepository
from src.app.shared.logging import BusinessLogger, get_logger


class DeleteStoryUseCase:
    """Use case for deleting a story."""

    def __init__(self, story_repository: StoryRepository):
        """
        Initialize use case.

        Args:
            story_repository: Story repository
        """
        self._repository = story_repository

    async def execute(self, story_id: str, created_by: str) -> bool:
        """
        Execute delete story use case.

        Args:
            story_id: Story UUID
            created_by: User ID performing the deletion

        Returns:
            True if deleted, False if not found
        """
        log = BusinessLogger(get_logger(__name__), user_id=created_by)

        try:
            # Get story details before deletion for logging
            entity = await self._repository.find_by_id(UUID(story_id))
            if not entity:
                log.failure("story.delete.not_found", entity_id=story_id)
                return False

            story_title = entity.title
            project_id = str(entity.project_id)

            deleted = await self._repository.delete(UUID(story_id))

            if deleted:
                log.event("story.deleted", entity_id=story_id, story_title=story_title, project_id=project_id)
            else:
                log.failure("story.delete.failed", entity_id=story_id)

            return deleted

        except Exception as e:
            log.failure("story.delete.unexpected_error", error=e, entity_id=story_id)
            raise
