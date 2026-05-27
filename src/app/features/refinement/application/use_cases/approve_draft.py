"""Approve draft use case - convert draft to story."""

from src.app.features.refinement.domain.entities.story_draft_entity import StoryDraftEntity
from src.app.features.refinement.domain.repositories.story_draft_repository import StoryDraftRepository
from src.app.features.stories.application.dtos.story_dto import StoryResponse
from src.app.features.stories.application.mappers.story_mapper import to_story_response
from src.app.features.stories.domain.entities.story_entity import StoryEntity
from src.app.features.stories.domain.repositories.story_repository import StoryRepository
from src.app.features.stories.domain.value_objects.story_priority import StoryPriority
from src.app.shared.domain.value_objects.entity_id import EntityId
from src.app.shared.logging import get_logger, log_business_event, log_error_event


log = get_logger(__name__)


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

    async def execute(self, draft_id: str) -> StoryResponse | None:
        """
        Execute approve draft use case.

        Converts a draft into a story and marks the draft as applied.

        Args:
            draft_id: Draft ID

        Returns:
            StoryResponse with created story data, or None if draft not found

        Raises:
            ValueError: If draft validation fails
        """
        try:
            draft_entity_id = EntityId.from_string(draft_id)
            draft = await self._draft_repository.find_by_id(draft_entity_id.value)

            if not draft:
                log.warning(
                    "Draft not found for approval",
                    extra={
                        "draft_id": draft_id,
                        "event_type": "refinement.approve.not_found",
                    },
                )
                return None

            story = await self._create_story_from_draft(draft)

            # Mark draft as applied to prevent duplicate story creation
            draft.mark_applied()
            await self._draft_repository.save(draft)

            log_business_event(
                logger=log,
                event_type="refinement.draft.approved",
                message="Draft approved and converted to story",
                entity_id=draft_id,
                additional_data={
                    "story_id": str(story.id.value),
                    "project_id": str(draft.project_id.value),
                    "story_title": story.title,
                },
            )

            return to_story_response(story)

        except Exception as e:
            log_error_event(
                logger=log,
                error_type="refinement.approve.failed",
                message="Failed to approve draft",
                error=e,
                additional_data={"draft_id": draft_id},
            )
            raise

    async def _create_story_from_draft(self, draft: StoryDraftEntity) -> StoryEntity:
        """
        Create a story entity from a draft.

        Args:
            draft: Story draft entity

        Returns:
            Created StoryEntity
        """
        # Merge description and acceptance criteria into structured description
        description_parts = []

        if draft.description:
            description_parts.append(draft.description)

        if draft.acceptance_criteria:
            description_parts.append("\n\n**Acceptance Criteria:**")
            for criterion in draft.acceptance_criteria:
                description_parts.append(f"- {criterion}")

        full_description = "\n".join(description_parts) if description_parts else None

        story = StoryEntity.create(
            title=draft.title,
            project_id=draft.project_id,
            created_by=draft.created_by,
            description=full_description,
            priority=StoryPriority.MEDIUM,
            points=None,
        )

        saved_story = await self._story_repository.save(story)

        if not saved_story:
            log_error_event(
                logger=log,
                error_type="refinement.approve.story_creation_failed",
                message="Failed to create story from draft",
                additional_data={
                    "draft_id": str(draft.id.value),
                    "project_id": str(draft.project_id.value),
                },
            )
            raise ValueError("Failed to create story from draft")

        return saved_story
