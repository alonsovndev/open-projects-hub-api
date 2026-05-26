"""Approve multiple drafts use case - bulk convert drafts to stories."""

from src.app.features.refinement.domain.entities.story_draft_entity import StoryDraftEntity
from src.app.features.refinement.domain.repositories.story_draft_repository import StoryDraftRepository
from src.app.features.stories.application.dtos.story_dto import StoryResponse
from src.app.features.stories.application.mappers.story_mapper import to_story_response
from src.app.features.stories.domain.entities.story_entity import StoryEntity
from src.app.features.stories.domain.repositories.story_repository import StoryRepository
from src.app.features.stories.domain.value_objects.story_priority import StoryPriority
from src.app.shared.domain.value_objects.entity_id import EntityId


class ApproveDraftsBulkUseCase:
    """Use case for approving multiple drafts and converting them to stories."""

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

    async def execute(self, draft_ids: list[str]) -> list[StoryResponse]:
        """
        Execute bulk approve drafts use case.

        Converts multiple drafts into stories and marks them as applied.

        Args:
            draft_ids: List of draft IDs

        Returns:
            List of StoryResponse with created story data

        Raises:
            ValueError: If any draft validation fails
        """
        if not draft_ids:
            return []

        created_stories: list[StoryResponse] = []

        for draft_id in draft_ids:
            draft_entity_id = EntityId.from_string(draft_id)
            draft = await self._draft_repository.find_by_id(draft_entity_id.value)

            if not draft:
                # Allow partial success - skip missing drafts instead of failing entire batch
                continue

            story = await self._create_story_from_draft(draft)

            # Mark draft as applied to prevent duplicate story creation
            draft.mark_applied()
            await self._draft_repository.save(draft)

            created_stories.append(to_story_response(story))

        return created_stories

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
            raise ValueError("Failed to create story from draft")

        return saved_story
