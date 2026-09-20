"""Delete story draft use case."""

from src.app.features.refinement.domain.exceptions.refinement_exceptions import StoryDraftNotFoundError
from src.app.features.refinement.domain.repositories.story_draft_repository import StoryDraftRepository
from src.app.shared.domain.value_objects.entity_id import EntityId
from src.app.shared.logging import get_logger, set_user_id


class DeleteStoryDraftUseCase:
    """Use case for discarding a story draft before it reaches the backlog."""

    def __init__(self, repository: StoryDraftRepository):
        """
        Initialize use case.

        Args:
            repository: Story draft repository
        """
        self._repository = repository

    async def execute(self, draft_id: str, deleted_by: str) -> None:
        """
        Delete a story draft.

        Args:
            draft_id: Draft UUID string
            deleted_by: User ID performing the deletion

        Raises:
            StoryDraftNotFoundError: If the draft is not found
        """
        log = get_logger(__name__)
        set_user_id(deleted_by)

        draft_uuid = EntityId.from_string(draft_id).value
        deleted = await self._repository.delete(draft_uuid)

        if not deleted:
            log.error(
                "Draft not found for deletion",
                extra={"event_type": "refinement.draft.delete.not_found", "entity_id": draft_id},
            )
            raise StoryDraftNotFoundError(draft_id)

        log.info("Story draft deleted", extra={"event_type": "refinement.draft.deleted", "entity_id": draft_id})
