"""Delete story draft use case."""

from src.app.features.refinement.domain.exceptions.refinement_exceptions import (
    StoryDraftAlreadyApprovedError,
    StoryDraftNotFoundError,
)
from src.app.features.refinement.domain.repositories.story_draft_repository import StoryDraftRepository
from src.app.features.refinement.domain.value_objects.draft_status import DraftStatus
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
            StoryDraftAlreadyApprovedError: If the draft is already in the backlog
        """
        log = get_logger(__name__)
        set_user_id(deleted_by)

        draft_uuid = EntityId.from_string(draft_id).value
        draft = await self._repository.find_by_id(draft_uuid)

        if not draft:
            log.error(
                "Draft not found for deletion",
                extra={"event_type": "refinement.draft.delete.not_found", "entity_id": draft_id},
            )
            raise StoryDraftNotFoundError(draft_id)

        # Discarding an applied draft would report success while leaving the story it
        # created sitting in the backlog, with nothing left to trace it back to.
        if draft.status is DraftStatus.APPLIED:
            log.warning(
                "Refused to discard an already-approved draft",
                extra={"event_type": "refinement.draft.delete.already_applied", "entity_id": draft_id},
            )
            raise StoryDraftAlreadyApprovedError(draft_id)

        deleted = await self._repository.delete(draft_uuid)

        if not deleted:
            log.error(
                "Draft not found for deletion",
                extra={"event_type": "refinement.draft.delete.not_found", "entity_id": draft_id},
            )
            raise StoryDraftNotFoundError(draft_id)

        log.info("Story draft deleted", extra={"event_type": "refinement.draft.deleted", "entity_id": draft_id})
