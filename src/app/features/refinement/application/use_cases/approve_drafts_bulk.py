"""Approve multiple drafts use case - bulk convert drafts to stories."""

from src.app.features.refinement.application.mappers.draft_to_story import draft_to_story_entity
from src.app.features.refinement.domain.repositories.story_draft_repository import StoryDraftRepository
from src.app.features.stories.application.dtos.story_dto import StoryResponse
from src.app.features.stories.application.mappers.story_mapper import to_story_response
from src.app.features.stories.domain.repositories.story_repository import StoryRepository
from src.app.shared.application.request_context import RequestContext
from src.app.shared.domain.value_objects.entity_id import EntityId
from src.app.shared.logging import get_logger, set_user_id


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

    async def execute(self, draft_ids: list[str], ctx: RequestContext) -> list[StoryResponse]:
        """
        Execute bulk approve drafts use case.

        Converts multiple drafts into stories and marks them as applied.

        Args:
            draft_ids: List of draft IDs
            ctx: Caller identity and workspace; drafts of other workspaces count as not found

        Returns:
            List of StoryResponse with created story data

        Raises:
            ValueError: If any draft validation fails
        """
        log = get_logger(__name__)
        set_user_id(str(ctx.user_id))

        if not draft_ids:
            log.warning(
                "Bulk approve called with empty draft list",
                extra={"event_type": "refinement.bulk_approve.empty_list"},
            )
            return []

        created_stories: list[StoryResponse] = []

        for draft_id in draft_ids:
            draft_entity_id = EntityId.from_string(draft_id)
            draft = await self._draft_repository.find_by_id(draft_entity_id.value, workspace_id=ctx.workspace_id.value)

            if not draft:
                log.warning(
                    "Draft not found in bulk approval",
                    extra={"event_type": "refinement.bulk_approve.draft_not_found", "entity_id": draft_id},
                )
                continue

            story_entity = draft_to_story_entity(draft)
            story = await self._story_repository.save(story_entity)

            if not story:
                raise ValueError("Failed to create story from draft")

            # Mark draft as applied to prevent duplicate story creation
            draft.mark_applied()
            await self._draft_repository.save(draft)

            log.info(
                "Draft approved and converted to story",
                extra={
                    "event_type": "refinement.draft.approved",
                    "entity_id": draft_id,
                    "story_id": str(story.id.value),
                    "project_id": str(draft.project_id.value),
                    "story_title": story.title,
                },
            )

            created_stories.append(to_story_response(story))

        if created_stories:
            log.info(
                "Bulk approval completed",
                extra={
                    "event_type": "refinement.bulk_approve.completed",
                    "approved_count": len(created_stories),
                },
            )
        else:
            log.warning(
                "No drafts were approved in bulk operation",
                extra={"event_type": "refinement.bulk_approve.no_results"},
            )

        return created_stories
