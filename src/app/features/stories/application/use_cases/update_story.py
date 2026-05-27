"""Update story use case."""

from uuid import UUID

from src.app.features.stories.application.dtos.story_dto import StoryResponse, UpdateStoryRequest
from src.app.features.stories.application.mappers.story_mapper import to_story_response
from src.app.features.stories.domain.repositories.story_repository import StoryRepository
from src.app.features.stories.domain.value_objects.story_priority import StoryPriority
from src.app.features.stories.domain.value_objects.story_status import StoryStatus
from src.app.shared.logging import get_logger, log_business_event, log_error_event


log = get_logger(__name__)


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
        try:
            entity = await self._repository.find_by_id(UUID(story_id))

            if not entity:
                log.warning(
                    "Story not found for update",
                    extra={
                        "story_id": story_id,
                        "event_type": "story.update.not_found",
                    },
                )
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
                    log_error_event(
                        logger=log,
                        error_type="story.update.invalid_status",
                        message="Invalid story status value",
                        error=e,
                        entity_id=story_id,
                        additional_data={"status": request.status},
                    )
                    raise ValueError(f"Invalid status '{request.status}'. Must be: todo, in_progress, done") from e

            # Validate priority enum early to provide clear user feedback
            story_priority = None
            if request.priority:
                try:
                    story_priority = StoryPriority(request.priority.lower())
                except ValueError as e:
                    log_error_event(
                        logger=log,
                        error_type="story.update.invalid_priority",
                        message="Invalid story priority value",
                        error=e,
                        entity_id=story_id,
                        additional_data={"priority": request.priority},
                    )
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
                log_error_event(
                    logger=log,
                    error_type="story.update.save_failed",
                    message="Failed to save updated story",
                    entity_id=story_id,
                )
                raise ValueError("Failed to update story")

            log_business_event(
                logger=log,
                event_type="story.updated",
                message="Story updated successfully",
                entity_id=story_id,
                additional_data={
                    "story_title": saved_entity.title,
                    "changes": changes,
                },
            )

            return to_story_response(saved_entity)

        except ValueError:
            raise
        except Exception as e:
            log_error_event(
                logger=log,
                error_type="story.update.unexpected_error",
                message="Unexpected error during story update",
                error=e,
                entity_id=story_id,
            )
            raise
