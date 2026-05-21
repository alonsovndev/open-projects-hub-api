"""
Tests for ApproveDraftUseCase.

Tests draft approval and story conversion.
"""
import pytest
from datetime import datetime
from unittest.mock import AsyncMock

from src.app.features.refinement.application.use_cases.approve_draft import ApproveDraftUseCase
from src.app.features.refinement.domain.entities.story_draft_entity import StoryDraftEntity
from src.app.features.refinement.domain.value_objects.refinement_status import RefinementStatus
from src.app.features.stories.application.dtos.story_dto import StoryResponse
from src.app.features.stories.domain.entities.story_entity import StoryEntity
from src.app.features.stories.domain.value_objects.story_priority import StoryPriority
from src.app.features.stories.domain.value_objects.story_status import StoryStatus
from src.app.shared.domain.value_objects.entity_id import EntityId


class TestApproveDraftUseCase:
    """Test ApproveDraftUseCase functionality."""

    @pytest.mark.asyncio
    async def test_execute_approves_draft_successfully(self):
        """Test successful draft approval creates story."""
        mock_draft_repo = AsyncMock()
        mock_story_repo = AsyncMock()

        draft_id = EntityId.generate()
        project_id = EntityId.generate()
        created_by = EntityId.generate()

        existing_draft = StoryDraftEntity(
            id=draft_id,
            title="Draft Title",
            description="Draft description",
            acceptance_criteria=["Criterion 1", "Criterion 2"],
            project_id=project_id,
            created_by=created_by,
            status=RefinementStatus.REFINED,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        mock_draft_repo.find_by_id.return_value = existing_draft

        created_story = StoryEntity(
            id=EntityId.generate(),
            title="Draft Title",
            description="Draft description\n\n**Acceptance Criteria:**\n- Criterion 1\n- Criterion 2",
            project_id=project_id,
            created_by=created_by,
            assigned_to=None,
            status=StoryStatus.TODO,
            priority=StoryPriority.MEDIUM,
            points=None,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        mock_story_repo.save.return_value = created_story
        mock_draft_repo.save.return_value = existing_draft

        use_case = ApproveDraftUseCase(mock_draft_repo, mock_story_repo)

        result = await use_case.execute(str(draft_id.value))

        assert result is not None
        assert isinstance(result, StoryResponse)
        assert result.title == "Draft Title"
        mock_story_repo.save.assert_called_once()
        mock_draft_repo.save.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_returns_none_when_draft_not_found(self):
        """Test that non-existent draft returns None."""
        mock_draft_repo = AsyncMock()
        mock_story_repo = AsyncMock()

        mock_draft_repo.find_by_id.return_value = None

        use_case = ApproveDraftUseCase(mock_draft_repo, mock_story_repo)

        result = await use_case.execute(str(EntityId.generate().value))

        assert result is None
        mock_story_repo.save.assert_not_called()

    @pytest.mark.asyncio
    async def test_execute_marks_draft_as_applied(self):
        """Test that draft is marked as applied after approval."""
        mock_draft_repo = AsyncMock()
        mock_story_repo = AsyncMock()

        draft_id = EntityId.generate()
        project_id = EntityId.generate()
        created_by = EntityId.generate()

        existing_draft = StoryDraftEntity(
            id=draft_id,
            title="Draft Title",
            description="Draft description",
            acceptance_criteria=[],
            project_id=project_id,
            created_by=created_by,
            status=RefinementStatus.REFINED,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        mock_draft_repo.find_by_id.return_value = existing_draft

        created_story = StoryEntity(
            id=EntityId.generate(),
            title="Draft Title",
            description="Draft description",
            project_id=project_id,
            created_by=created_by,
            assigned_to=None,
            status=StoryStatus.TODO,
            priority=StoryPriority.MEDIUM,
            points=None,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        mock_story_repo.save.return_value = created_story
        mock_draft_repo.save.return_value = existing_draft

        use_case = ApproveDraftUseCase(mock_draft_repo, mock_story_repo)

        await use_case.execute(str(draft_id.value))

        assert existing_draft.status == RefinementStatus.APPLIED

    @pytest.mark.asyncio
    async def test_execute_raises_error_when_story_save_fails(self):
        """Test that story save failure raises ValueError."""
        mock_draft_repo = AsyncMock()
        mock_story_repo = AsyncMock()

        draft_id = EntityId.generate()
        project_id = EntityId.generate()
        created_by = EntityId.generate()

        existing_draft = StoryDraftEntity(
            id=draft_id,
            title="Draft Title",
            description="Draft description",
            acceptance_criteria=[],
            project_id=project_id,
            created_by=created_by,
            status=RefinementStatus.REFINED,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        mock_draft_repo.find_by_id.return_value = existing_draft
        mock_story_repo.save.return_value = None

        use_case = ApproveDraftUseCase(mock_draft_repo, mock_story_repo)

        with pytest.raises(ValueError, match="Failed to create story from draft"):
            await use_case.execute(str(draft_id.value))

    @pytest.mark.asyncio
    async def test_execute_creates_story_with_description_and_criteria(self):
        """Test that story description includes acceptance criteria."""
        mock_draft_repo = AsyncMock()
        mock_story_repo = AsyncMock()

        draft_id = EntityId.generate()
        project_id = EntityId.generate()
        created_by = EntityId.generate()

        existing_draft = StoryDraftEntity(
            id=draft_id,
            title="Draft Title",
            description="User needs to login",
            acceptance_criteria=["User can enter credentials", "User sees dashboard"],
            project_id=project_id,
            created_by=created_by,
            status=RefinementStatus.REFINED,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        mock_draft_repo.find_by_id.return_value = existing_draft

        created_story = StoryEntity(
            id=EntityId.generate(),
            title="Draft Title",
            description="User needs to login\n\n**Acceptance Criteria:**\n- User can enter credentials\n- User sees dashboard",
            project_id=project_id,
            created_by=created_by,
            assigned_to=None,
            status=StoryStatus.TODO,
            priority=StoryPriority.MEDIUM,
            points=None,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        mock_story_repo.save.return_value = created_story
        mock_draft_repo.save.return_value = existing_draft

        use_case = ApproveDraftUseCase(mock_draft_repo, mock_story_repo)

        result = await use_case.execute(str(draft_id.value))

        assert result is not None
        assert "Acceptance Criteria" in result.description
        assert "User can enter credentials" in result.description

    @pytest.mark.asyncio
    async def test_execute_creates_story_without_description(self):
        """Test that story can be created without description."""
        mock_draft_repo = AsyncMock()
        mock_story_repo = AsyncMock()

        draft_id = EntityId.generate()
        project_id = EntityId.generate()
        created_by = EntityId.generate()

        existing_draft = StoryDraftEntity(
            id=draft_id,
            title="Draft Title",
            description=None,
            acceptance_criteria=[],
            project_id=project_id,
            created_by=created_by,
            status=RefinementStatus.REFINED,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        mock_draft_repo.find_by_id.return_value = existing_draft

        created_story = StoryEntity(
            id=EntityId.generate(),
            title="Draft Title",
            description=None,
            project_id=project_id,
            created_by=created_by,
            assigned_to=None,
            status=StoryStatus.TODO,
            priority=StoryPriority.MEDIUM,
            points=None,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        mock_story_repo.save.return_value = created_story
        mock_draft_repo.save.return_value = existing_draft

        use_case = ApproveDraftUseCase(mock_draft_repo, mock_story_repo)

        result = await use_case.execute(str(draft_id.value))

        assert result is not None
        assert result.description is None
