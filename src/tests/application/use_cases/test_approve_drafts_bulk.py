"""
Tests for ApproveDraftsBulkUseCase.

Tests bulk draft approval and story conversion.
"""

from datetime import UTC, datetime
from unittest.mock import AsyncMock

import pytest

from src.app.features.refinement.application.use_cases.approve_drafts_bulk import ApproveDraftsBulkUseCase
from src.app.features.refinement.domain.entities.story_draft_entity import StoryDraftEntity
from src.app.features.refinement.domain.value_objects.draft_status import DraftStatus
from src.app.features.stories.application.dtos.story_dto import StoryResponse
from src.app.features.stories.domain.entities.story_entity import StoryEntity
from src.app.features.stories.domain.value_objects.story_priority import StoryPriority
from src.app.features.stories.domain.value_objects.story_status import StoryStatus
from src.app.shared.domain.value_objects.entity_id import EntityId
from src.tests.support.request_context import make_request_context


class TestApproveDraftsBulkUseCase:
    """Test ApproveDraftsBulkUseCase functionality."""

    @pytest.mark.asyncio
    async def test_execute_approves_multiple_drafts_successfully(self):
        """Test successful bulk approval of multiple drafts."""
        mock_draft_repo = AsyncMock()
        mock_story_repo = AsyncMock()

        draft_id_1 = EntityId.generate()
        draft_id_2 = EntityId.generate()
        project_id = EntityId.generate()
        created_by = EntityId.generate()

        draft_1 = StoryDraftEntity(
            id=draft_id_1,
            title="Draft 1",
            description="Description 1",
            acceptance_criteria=["Criterion 1"],
            project_id=project_id,
            created_by=created_by,
            status=DraftStatus.DRAFT,
            created_at=datetime.now(tz=UTC),
            updated_at=datetime.now(tz=UTC),
        )
        draft_2 = StoryDraftEntity(
            id=draft_id_2,
            title="Draft 2",
            description="Description 2",
            acceptance_criteria=["Criterion 2"],
            project_id=project_id,
            created_by=created_by,
            status=DraftStatus.DRAFT,
            created_at=datetime.now(tz=UTC),
            updated_at=datetime.now(tz=UTC),
        )

        def find_side_effect(draft_id, **_scope):
            if draft_id == draft_id_1.value:
                return draft_1
            if draft_id == draft_id_2.value:
                return draft_2
            return None

        mock_draft_repo.find_by_id.side_effect = find_side_effect

        def save_side_effect(entity):
            if isinstance(entity, StoryEntity):
                return entity
            return entity

        mock_story_repo.save.side_effect = save_side_effect
        mock_draft_repo.save.side_effect = save_side_effect

        use_case = ApproveDraftsBulkUseCase(mock_draft_repo, mock_story_repo)

        result = await use_case.execute([str(draft_id_1.value), str(draft_id_2.value)], ctx=make_request_context())

        assert len(result) == 2
        assert isinstance(result[0], StoryResponse)
        assert result[0].title == "Draft 1"
        assert result[1].title == "Draft 2"
        assert mock_story_repo.save.call_count == 2

    @pytest.mark.asyncio
    async def test_execute_returns_empty_list_for_empty_draft_ids(self):
        """Test that empty draft_ids returns empty list."""
        mock_draft_repo = AsyncMock()
        mock_story_repo = AsyncMock()

        use_case = ApproveDraftsBulkUseCase(mock_draft_repo, mock_story_repo)

        result = await use_case.execute([], ctx=make_request_context())

        assert result == []
        mock_draft_repo.find_by_id.assert_not_called()

    @pytest.mark.asyncio
    async def test_execute_partial_success_skips_missing_drafts(self):
        """Test that missing drafts are skipped (partial success)."""
        mock_draft_repo = AsyncMock()
        mock_story_repo = AsyncMock()

        draft_id_1 = EntityId.generate()
        missing_draft_id = EntityId.generate()
        project_id = EntityId.generate()
        created_by = EntityId.generate()

        draft_1 = StoryDraftEntity(
            id=draft_id_1,
            title="Draft 1",
            description="Description 1",
            acceptance_criteria=[],
            project_id=project_id,
            created_by=created_by,
            status=DraftStatus.DRAFT,
            created_at=datetime.now(tz=UTC),
            updated_at=datetime.now(tz=UTC),
        )

        def find_side_effect(draft_id, **_scope):
            if draft_id == draft_id_1.value:
                return draft_1
            return None

        mock_draft_repo.find_by_id.side_effect = find_side_effect

        story_1 = StoryEntity(
            id=EntityId.generate(),
            title="Draft 1",
            description="Description 1",
            project_id=project_id,
            created_by=created_by,
            assigned_to=None,
            status=StoryStatus.TODO,
            priority=StoryPriority.MEDIUM,
            points=None,
            created_at=datetime.now(tz=UTC),
            updated_at=datetime.now(tz=UTC),
        )
        mock_story_repo.save.return_value = story_1
        mock_draft_repo.save.return_value = draft_1

        use_case = ApproveDraftsBulkUseCase(mock_draft_repo, mock_story_repo)

        result = await use_case.execute(
            [str(draft_id_1.value), str(missing_draft_id.value)], ctx=make_request_context()
        )

        assert len(result) == 1
        assert result[0].title == "Draft 1"

    @pytest.mark.asyncio
    async def test_execute_all_drafts_missing_returns_empty_list(self):
        """Test that all missing drafts returns empty list."""
        mock_draft_repo = AsyncMock()
        mock_story_repo = AsyncMock()

        mock_draft_repo.find_by_id.return_value = None

        use_case = ApproveDraftsBulkUseCase(mock_draft_repo, mock_story_repo)

        result = await use_case.execute(
            [str(EntityId.generate().value), str(EntityId.generate().value)], ctx=make_request_context()
        )

        assert result == []
        mock_story_repo.save.assert_not_called()

    @pytest.mark.asyncio
    async def test_execute_marks_all_drafts_as_applied(self):
        """Test that all approved drafts are marked as applied."""
        mock_draft_repo = AsyncMock()
        mock_story_repo = AsyncMock()

        draft_id_1 = EntityId.generate()
        draft_id_2 = EntityId.generate()
        project_id = EntityId.generate()
        created_by = EntityId.generate()

        draft_1 = StoryDraftEntity(
            id=draft_id_1,
            title="Draft 1",
            description="Description 1",
            acceptance_criteria=[],
            project_id=project_id,
            created_by=created_by,
            status=DraftStatus.DRAFT,
            created_at=datetime.now(tz=UTC),
            updated_at=datetime.now(tz=UTC),
        )
        draft_2 = StoryDraftEntity(
            id=draft_id_2,
            title="Draft 2",
            description="Description 2",
            acceptance_criteria=[],
            project_id=project_id,
            created_by=created_by,
            status=DraftStatus.DRAFT,
            created_at=datetime.now(tz=UTC),
            updated_at=datetime.now(tz=UTC),
        )

        def find_side_effect(draft_id, **_scope):
            if draft_id == draft_id_1.value:
                return draft_1
            if draft_id == draft_id_2.value:
                return draft_2
            return None

        mock_draft_repo.find_by_id.side_effect = find_side_effect

        story_1 = StoryEntity(
            id=EntityId.generate(),
            title="Draft 1",
            description="Description 1",
            project_id=project_id,
            created_by=created_by,
            assigned_to=None,
            status=StoryStatus.TODO,
            priority=StoryPriority.MEDIUM,
            points=None,
            created_at=datetime.now(tz=UTC),
            updated_at=datetime.now(tz=UTC),
        )
        story_2 = StoryEntity(
            id=EntityId.generate(),
            title="Draft 2",
            description="Description 2",
            project_id=project_id,
            created_by=created_by,
            assigned_to=None,
            status=StoryStatus.TODO,
            priority=StoryPriority.MEDIUM,
            points=None,
            created_at=datetime.now(tz=UTC),
            updated_at=datetime.now(tz=UTC),
        )

        def save_side_effect(entity):
            return entity

        mock_story_repo.save.side_effect = [story_1, story_2]
        mock_draft_repo.save.side_effect = save_side_effect

        use_case = ApproveDraftsBulkUseCase(mock_draft_repo, mock_story_repo)

        await use_case.execute([str(draft_id_1.value), str(draft_id_2.value)], ctx=make_request_context())

        assert draft_1.status == DraftStatus.APPLIED
        assert draft_2.status == DraftStatus.APPLIED

    @pytest.mark.asyncio
    async def test_execute_raises_error_when_story_save_fails(self):
        """Test that story save failure raises ValueError."""
        mock_draft_repo = AsyncMock()
        mock_story_repo = AsyncMock()

        draft_id = EntityId.generate()
        project_id = EntityId.generate()
        created_by = EntityId.generate()

        draft = StoryDraftEntity(
            id=draft_id,
            title="Draft",
            description="Description",
            acceptance_criteria=[],
            project_id=project_id,
            created_by=created_by,
            status=DraftStatus.DRAFT,
            created_at=datetime.now(tz=UTC),
            updated_at=datetime.now(tz=UTC),
        )
        mock_draft_repo.find_by_id.return_value = draft
        mock_story_repo.save.return_value = None

        use_case = ApproveDraftsBulkUseCase(mock_draft_repo, mock_story_repo)

        with pytest.raises(ValueError, match="Failed to create story from draft"):
            await use_case.execute([str(draft_id.value)], ctx=make_request_context())
