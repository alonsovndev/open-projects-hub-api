"""Update story draft use case."""

from src.app.features.refinement.application.dtos.refinement_dto import UpdateStoryDraftRequest
from src.app.features.refinement.domain.entities.story_draft_entity import StoryDraftEntity
from src.app.features.refinement.domain.repositories.story_draft_repository import StoryDraftRepository
from src.app.shared.domain.value_objects.entity_id import EntityId
from src.app.shared.logging import BusinessLogger, get_logger


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
        created_by: str,
    ) -> StoryDraftEntity | None:
        """
        Execute update story draft use case.

        Args:
            draft_id: Draft UUID string
            request: UpdateStoryDraftRequest with fields to update
            created_by: User ID performing the update

        Returns:
            StoryDraftEntity if updated, None if not found
        """
        log = BusinessLogger(get_logger(__name__), user_id=created_by)

        entity_id = EntityId.from_string(draft_id)
        draft = await self._repository.find_by_id(entity_id.value)

        if not draft:
            log.failure("refinement.draft.update.not_found", entity_id=draft_id)
            return None

        draft.update_draft(
            title=request.title,
            description=request.description,
            acceptance_criteria=request.acceptance_criteria,
        )

        updated = await self._repository.save(draft)

        log.event("refinement.draft.updated", entity_id=draft_id)

        return updated
