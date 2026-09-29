"""Create story use case."""

from src.app.features.projects.domain.repositories.project_repository import ProjectRepository
from src.app.features.stories.application.dtos.story_dto import CreateStoryRequest, StoryResponse
from src.app.features.stories.application.mappers.story_mapper import to_story_response
from src.app.features.stories.domain.entities.story_entity import StoryEntity
from src.app.features.stories.domain.repositories.story_repository import StoryRepository
from src.app.features.stories.domain.value_objects.story_priority import StoryPriority
from src.app.shared.application.request_context import RequestContext
from src.app.shared.domain.exceptions.domain_exceptions import NotFoundError
from src.app.shared.domain.value_objects.entity_id import EntityId
from src.app.shared.logging import get_logger, set_user_id


class CreateStoryUseCase:
    """Use case for creating a new story."""

    def __init__(self, story_repository: StoryRepository, project_repository: ProjectRepository):
        """
        Initialize use case.

        Args:
            story_repository: Story repository
            project_repository: Project repository, to confirm the target project is the caller's
        """
        self._repository = story_repository
        self._project_repository = project_repository

    async def execute(self, request: CreateStoryRequest, ctx: RequestContext) -> StoryResponse:
        """
        Execute create story use case.

        Args:
            request: CreateStoryRequest DTO with story data
            ctx: Caller identity and workspace (from JWT token)

        Returns:
            StoryResponse with created story data

        Raises:
            ValidationError: If validation fails
            NotFoundError: If the project is not in the caller's workspace
        """
        log = get_logger(__name__)
        set_user_id(str(ctx.user_id))

        project_id = EntityId.from_string(request.project_id)
        if not await self._project_repository.exists(project_id.value, workspace_id=ctx.workspace_id.value):
            raise NotFoundError("Project", request.project_id)

        story_priority = StoryPriority(request.priority) if request.priority else None

        entity = StoryEntity.create(
            title=request.title,
            project_id=project_id,
            created_by=ctx.user_id,
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
