"""Create story use case."""

from src.app.features.stories.application.dtos.story_dto import CreateStoryRequest, StoryResponse
from src.app.features.stories.application.mappers.story_mapper import to_story_response
from src.app.features.stories.domain.entities.story_entity import StoryEntity
from src.app.features.stories.domain.repositories.story_repository import StoryRepository
from src.app.features.stories.domain.value_objects.story_priority import StoryPriority
from src.app.shared.domain.value_objects.entity_id import EntityId
from src.app.shared.logging import get_logger, set_user_id


class CreateStoryUseCase:
    """Use case for creating a new story."""

    def __init__(self, story_repository: StoryRepository):
        """
        Initialize use case.

        Args:
            story_repository: Story repository
        """
        self._repository = story_repository

    async def execute(self, request: CreateStoryRequest, created_by: str) -> StoryResponse:
        """
        Execute create story use case.

        Args:
            request: CreateStoryRequest DTO with story data
            created_by: User ID of creator (from JWT token)

        Returns:
            StoryResponse with created story data

        Raises:
            ValidationError: If validation fails
        """
        log = get_logger(__name__)
        set_user_id(created_by)

        story_priority = StoryPriority(request.priority) if request.priority else None

        entity = StoryEntity.create(
            title=request.title,
            project_id=EntityId.from_string(request.project_id),
            created_by=EntityId.from_string(created_by),
            description=request.description,
            priority=story_priority,
            points=request.points,
            acceptance_criteria=request.acceptance_criteria,
        )

        saved_entity = await self._repository.save(entity)

        if not saved_entity:
            log.error(
                "Failed to save story",
                extra={
                    "event_type": "story.create.save_failed",
                    "story_title": request.title,
                    "project_id": request.project_id,
                },
            )
            raise RuntimeError("Failed to create story")

        log.info(
            "Story created",
            extra={
                "event_type": "story.created",
                "entity_id": str(saved_entity.id),
                "story_title": saved_entity.title,
                "project_id": str(saved_entity.project_id),
                "priority": saved_entity.priority.value if saved_entity.priority else None,
                "points": saved_entity.points,
            },
        )

        return to_story_response(saved_entity)
