"""Tests for ListStoryDraftsUseCase."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock

import pytest

from src.app.features.refinement.application.use_cases.list_story_drafts import ListStoryDraftsUseCase
from src.app.features.refinement.domain.entities.story_draft_entity import StoryDraftEntity
from src.app.features.refinement.domain.value_objects.draft_status import DraftStatus
from src.app.shared.domain.value_objects.entity_id import EntityId


def build_draft(project_id: EntityId, status: DraftStatus = DraftStatus.DRAFT) -> StoryDraftEntity:
    """Build a persisted-looking draft entity for a project."""
    return StoryDraftEntity(
        id=EntityId.generate(),
        title="Draft title",
        description="As an Admin, I want to export the backlog.",
        acceptance_criteria=["Export includes approved stories only"],
        project_id=project_id,
        created_by=EntityId.generate(),
        status=status,
        created_at=datetime.now(tz=UTC),
        updated_at=datetime.now(tz=UTC),
    )


class TestListStoryDraftsUseCase:
    """Test draft listing behavior."""

    @pytest.mark.asyncio
    async def test_execute_returns_drafts_with_total(self):
        """Test that drafts are mapped to DTOs alongside the matching total."""
        project_id = EntityId.generate()
        mock_repo = AsyncMock()
        mock_repo.find_by_project.return_value = [build_draft(project_id), build_draft(project_id)]
        mock_repo.count_by_project.return_value = 2

        use_case = ListStoryDraftsUseCase(mock_repo)
        result = await use_case.execute(project_id=str(project_id.value))

        assert result.total == 2
        assert len(result.drafts) == 2
        assert result.drafts[0].project_id == str(project_id.value)
        assert result.drafts[0].status == DraftStatus.DRAFT.value

    @pytest.mark.asyncio
    async def test_execute_passes_status_filter_through(self):
        """Test that a status filter reaches both the query and the count."""
        project_id = EntityId.generate()
        mock_repo = AsyncMock()
        mock_repo.find_by_project.return_value = []
        mock_repo.count_by_project.return_value = 0

        use_case = ListStoryDraftsUseCase(mock_repo)
        await use_case.execute(project_id=str(project_id.value), status=DraftStatus.DRAFT)

        assert mock_repo.find_by_project.call_args.kwargs["status"] is DraftStatus.DRAFT
        assert mock_repo.count_by_project.call_args.kwargs["status"] is DraftStatus.DRAFT
