"""Assign story use case."""

from uuid import UUID

from src.app.features.stories.application.dtos.story_dto import StoryResponse
from src.app.features.stories.application.mappers.story_mapper import to_story_response
from src.app.features.stories.domain.exceptions.story_exceptions import StoryNotFoundError
from src.app.features.stories.domain.repositories.story_repository import StoryRepository
from src.app.features.user.domain.repositories.user_repository import UserRepository
from src.app.shared.application.request_context import RequestContext
from src.app.shared.domain.exceptions.domain_exceptions import NotFoundError
from src.app.shared.domain.value_objects.entity_id import EntityId
from src.app.shared.logging import get_logger, set_user_id


class AssignStoryUseCase:
    """Use case for assigning a story to a user."""

    def __init__(self, story_repository: StoryRepository, user_repository: UserRepository):
        """
        Initialize use case.

        Args:
            story_repository: Story repository
            user_repository: User repository, to confirm the assignee is a teammate
        """
        self._repository = story_repository
        self._user_repository = user_repository

    async def execute(self, story_id: str, user_id: str, ctx: RequestContext) -> StoryResponse:
        """
        Execute assign story use case.

        Args:
            story_id: Story UUID
            user_id: User UUID to assign
            ctx: Caller identity and workspace

        Returns:
            StoryResponse with updated story data

        Raises:
            StoryNotFoundError: If story not found
            NotFoundError: If the assignee is not in the caller's workspace
        """
        log = get_logger(__name__)
        set_user_id(str(ctx.user_id))

        entity = await self._repository.find_by_id(UUID(story_id), workspace_id=ctx.workspace_id.value)

        if not entity:
            log.error(
                "Story not found for assignment",
                extra={"event_type": "story.assign.not_found", "entity_id": story_id, "assigned_to": user_id},
            )
            raise StoryNotFoundError(story_id)

        # Track previous assignment for logging
        previous_assignee = str(entity.assigned_to) if entity.assigned_to else None

        assignee_id = EntityId.from_string(user_id)
        assignee = await self._user_repository.find_by_id(assignee_id)
        if assignee is None or not assignee.belongs_to(ctx.workspace_id):
            raise NotFoundError("User", user_id)

        entity.assign_to(assignee_id)

        saved_entity = await self._repository.save(entity)

        if not saved_entity:
            log.error(
                "Failed to save story assignment",
                extra={"event_type": "story.assign.save_failed", "assigned_to": user_id},
            )
            raise RuntimeError("Failed to assign story")

        log.info(
            "Story assigned",
            extra={
                "event_type": "story.assigned",
                "entity_id": story_id,
                "story_title": saved_entity.title,
                "assigned_to": user_id,
                "previous_assignee": previous_assignee,
            },
        )

        return to_story_response(saved_entity)
