"""Update story use case."""

from uuid import UUID

from src.app.features.stories.application.dtos.story_dto import StoryResponse, UpdateStoryRequest
from src.app.features.stories.application.mappers.story_mapper import to_story_response
from src.app.features.stories.domain.repositories.story_repository import StoryRepository
from src.app.features.stories.domain.value_objects.story_priority import StoryPriority
from src.app.features.stories.domain.value_objects.story_status import StoryStatus
from src.app.shared.logging import BusinessLogger, get_logger


class UpdateStoryUseCase:
    """Use case for updating a story."""

    def __init__(self, story_repository: StoryRepository):
        """
        Initialize use case.

        Args:
            story_repository: Story repository
        """
        self._repository = story_repository

    async def execute(self, story_id: str, request: UpdateStoryRequest, created_by: str) -> StoryResponse | None:
        """
        Execute update story use case.

        Args:
            story_id: Story UUID
            request: UpdateStoryRequest DTO with fields to update
            created_by: User ID performing the update

        Returns:
            StoryResponse if found and updated, None otherwise

        Raises:
            ValueError: If validation fails
        """
        log = BusinessLogger(get_logger(__name__), user_id=created_by)

        try:
            entity = await self._repository.find_by_id(UUID(story_id))

            if not entity:
                log.failure("story.update.not_found", entity_id=story_id)
                return None

            # Track changes for logging
            changes = {}
            if request.title and request.title != entity.title:
                changes["title"] = {"old": entity.title, "new": request.title}
            if request.status and request.status.lower() != entity.status.value:
                changes["status"] = {"old": entity.status.value, "new": request.status.lower()}
            if request.priority and request.priority.lower() != (entity.priority.value if entity.priority else None):
                changes["priority"] = {
                    "old": entity.priority.value if entity.priority else None,
                    "new": request.priority.lower(),
                }

            # Validate status enum early to provide clear user feedback
            story_status = None
            if request.status:
                try:
                    story_status = StoryStatus(request.status.lower())
                except ValueError as e:
                    log.failure("story.update.invalid_status", error=e, entity_id=story_id, status=request.status)
                    raise ValueError(f"Invalid status '{request.status}'. Must be: todo, in_progress, done") from e

            # Validate priority enum early to provide clear user feedback
            story_priority = None
            if request.priority:
                try:
                    story_priority = StoryPriority(request.priority.lower())
                except ValueError as e:
                    log.failure("story.update.invalid_priority", error=e, entity_id=story_id, priority=request.priority)
                    raise ValueError(f"Invalid priority '{request.priority}'. Must be: low, medium, high") from e

            entity.update_details(
                title=request.title,
                description=request.description,
                status=story_status,
                priority=story_priority,
                points=request.points,
            )

            saved_entity = await self._repository.save(entity)

            if not saved_entity:
                log.failure("story.update.save_failed", entity_id=story_id)
                raise ValueError("Failed to update story")

            log.event("story.updated", entity_id=story_id, story_title=saved_entity.title, changes=changes)

            return to_story_response(saved_entity)

        except ValueError:
            raise
        except Exception as e:
            log.failure("story.update.unexpected_error", error=e, entity_id=story_id)
            raise
