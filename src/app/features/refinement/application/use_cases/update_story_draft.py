"""Update story draft use case."""

from src.app.features.refinement.application.dtos.refinement_dto import UpdateStoryDraftRequest
from src.app.features.refinement.domain.entities.story_draft_entity import StoryDraftEntity
from src.app.features.refinement.domain.exceptions.refinement_exceptions import StoryDraftNotFoundError
from src.app.features.refinement.domain.repositories.story_draft_repository import StoryDraftRepository
from src.app.shared.application.request_context import RequestContext
from src.app.shared.domain.value_objects.entity_id import EntityId
from src.app.shared.logging import get_logger, set_user_id


class UpdateStoryDraftUseCase:
    """Use case for updating a story draft."""

    def __init__(self, repository: StoryDraftRepository):
        """
        Initialize use case.

        Args:
            repository: Story draft repository
        """
        self._repository = repository

    async def execute(
        self,
        draft_id: str,
        request: UpdateStoryDraftRequest,
        ctx: RequestContext,
    ) -> StoryDraftEntity:
        """
        Execute update story draft use case.

        Args:
            draft_id: Draft UUID string
            request: UpdateStoryDraftRequest with fields to update
            ctx: Caller identity and workspace

        Returns:
            Updated StoryDraftEntity

        Raises:
            StoryDraftNotFoundError: If the draft is not found
        """
        log = get_logger(__name__)
        set_user_id(str(ctx.user_id))

        entity_id = EntityId.from_string(draft_id)
        draft = await self._repository.find_by_id(entity_id.value, workspace_id=ctx.workspace_id.value)

        if not draft:
            log.error(
                "Draft not found for update",
                extra={"event_type": "refinement.draft.update.not_found", "entity_id": draft_id},
            )
            raise StoryDraftNotFoundError(draft_id)

        draft.update_draft(
            title=request.title,
            description=request.description,
            acceptance_criteria=request.acceptance_criteria,
        )

        updated = await self._repository.save(draft)

        log.info("Story draft updated", extra={"event_type": "refinement.draft.updated", "entity_id": draft_id})

        return updated
