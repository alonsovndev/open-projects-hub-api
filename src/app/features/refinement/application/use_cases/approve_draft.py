"""Approve draft use case - convert draft to story."""

from src.app.features.refinement.application.mappers.draft_to_story import draft_to_story_entity
from src.app.features.refinement.domain.exceptions.refinement_exceptions import StoryDraftNotFoundError
from src.app.features.refinement.domain.repositories.story_draft_repository import StoryDraftRepository
from src.app.features.stories.application.dtos.story_dto import StoryResponse
from src.app.features.stories.application.mappers.story_mapper import to_story_response
from src.app.features.stories.domain.repositories.story_repository import StoryRepository
from src.app.shared.domain.value_objects.entity_id import EntityId
from src.app.shared.logging import BusinessLogger, get_logger


class ApproveDraftUseCase:
    """Use case for approving a draft and converting it to a story."""

    def __init__(
        self,
        draft_repository: StoryDraftRepository,
        story_repository: StoryRepository,
    ):
        """
        Initialize use case.

        Args:
            draft_repository: Story draft repository
            story_repository: Story repository
        """
        self._draft_repository = draft_repository
        self._story_repository = story_repository

    async def execute(self, draft_id: str, created_by: str) -> StoryResponse:
        """
        Execute approve draft use case.

        Converts a draft into a story and marks the draft as applied.

        Args:
            draft_id: Draft ID
            created_by: User ID approving the draft

        Returns:
            StoryResponse with created story data

        Raises:
            StoryDraftNotFoundError: If the draft is not found
            ValueError: If draft validation fails
        """
        log = BusinessLogger(get_logger(__name__), user_id=created_by)

        try:
            draft_entity_id = EntityId.from_string(draft_id)
            draft = await self._draft_repository.find_by_id(draft_entity_id.value)

            if not draft:
                log.failure("refinement.approve.not_found", entity_id=draft_id)
                raise StoryDraftNotFoundError(draft_id)

            story_entity = draft_to_story_entity(draft)
            story = await self._story_repository.save(story_entity)

            if not story:
                raise ValueError("Failed to create story from draft")

            # Mark draft as applied to prevent duplicate story creation
            draft.mark_applied()
            await self._draft_repository.save(draft)

            log.event(
                "refinement.draft.approved",
                entity_id=draft_id,
                story_id=str(story.id.value),
                project_id=str(draft.project_id.value),
                story_title=story.title,
            )

            return to_story_response(story)

        except StoryDraftNotFoundError:
            raise
        except Exception as e:
            log.failure("refinement.approve.failed", error=e, entity_id=draft_id)
            raise
