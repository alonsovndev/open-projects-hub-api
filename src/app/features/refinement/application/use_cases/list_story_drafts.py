"""List story drafts for a project use case."""

from src.app.features.refinement.application.dtos.refinement_dto import ListStoryDraftsResponse
from src.app.features.refinement.application.mappers.story_draft_mapper import to_story_draft_response
from src.app.features.refinement.domain.repositories.story_draft_repository import StoryDraftRepository
from src.app.features.refinement.domain.value_objects.draft_status import DraftStatus
from src.app.shared.application.request_context import RequestContext
from src.app.shared.domain.value_objects.entity_id import EntityId


class ListStoryDraftsUseCase:
    """Use case for listing a project's story drafts."""

    def __init__(self, repository: StoryDraftRepository):
        """
        Initialize use case.

        Args:
            repository: Story draft repository
        """
        self._repository = repository

    async def execute(
        self,
        project_id: str,
        ctx: RequestContext,
        status: DraftStatus | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> ListStoryDraftsResponse:
        """
        List story drafts for a project.

        Args:
            project_id: Project UUID string
            ctx: Caller identity and workspace
            status: Restrict to a single draft status, or None for all
            limit: Maximum results
            offset: Number to skip

        Returns:
            ListStoryDraftsResponse with the page of drafts and the matching total
        """
        project_uuid = EntityId.from_string(project_id).value

        workspace_id = ctx.workspace_id.value
        drafts = await self._repository.find_by_project(
            project_id=project_uuid,
            workspace_id=workspace_id,
            status=status,
            limit=limit,
            offset=offset,
        )
        total = await self._repository.count_by_project(project_uuid, workspace_id=workspace_id, status=status)

        return ListStoryDraftsResponse(
            drafts=[to_story_draft_response(draft) for draft in drafts],
            total=total,
        )
