"""
Tests for UpdateStoryDraftUseCase.

Tests draft update including validation and error handling.
"""

from datetime import datetime
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from pydantic import ValidationError

from src.app.features.refinement.application.dtos.refinement_dto import UpdateStoryDraftRequest
from src.app.features.refinement.application.use_cases.update_story_draft import UpdateStoryDraftUseCase
from src.app.features.refinement.domain.entities.story_draft_entity import StoryDraftEntity
from src.app.features.refinement.domain.value_objects.refinement_status import RefinementStatus
from src.app.shared.domain.value_objects.entity_id import EntityId


class TestUpdateStoryDraftUseCase:
    """Test UpdateStoryDraftUseCase functionality."""

    @pytest.mark.asyncio
    async def test_execute_updates_draft_successfully(self):
        """Test successful draft update."""
        mock_repo = AsyncMock()
        draft_id = EntityId.generate()

        existing_draft = StoryDraftEntity(
            id=draft_id,
            title="Old Title",
            description="Old description",
            acceptance_criteria=["Old criterion"],
            project_id=EntityId.generate(),
            created_by=EntityId.generate(),
            status=RefinementStatus.DRAFT,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        mock_repo.find_by_id.return_value = existing_draft

        updated_draft = StoryDraftEntity(
            id=draft_id,
            title="New Title",
            description="New description",
            acceptance_criteria=["New criterion"],
            project_id=existing_draft.project_id,
            created_by=existing_draft.created_by,
            status=RefinementStatus.DRAFT,
            created_at=existing_draft.created_at,
            updated_at=datetime.now(),
        )
        mock_repo.save.return_value = updated_draft

        use_case = UpdateStoryDraftUseCase(mock_repo)

        request = UpdateStoryDraftRequest(
            title="New Title",
            description="New description",
            acceptance_criteria=["New criterion"],
        )
        result = await use_case.execute(
            draft_id=str(draft_id.value),
            request=request,
        )

        assert result is not None
        assert result.title == "New Title"
        assert result.description == "New description"
        mock_repo.save.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_returns_none_when_draft_not_found(self):
        """Test that non-existent draft returns None."""
        mock_repo = AsyncMock()
        mock_repo.find_by_id.return_value = None

        use_case = UpdateStoryDraftUseCase(mock_repo)

        request = UpdateStoryDraftRequest(title="New Title")
        result = await use_case.execute(
            draft_id=str(uuid4()),
            request=request,
        )

        assert result is None
        mock_repo.save.assert_not_called()

    @pytest.mark.asyncio
    async def test_execute_raises_error_on_empty_title(self):
        """Test that empty title raises ValidationError at DTO level."""
        mock_repo = AsyncMock()
        use_case = UpdateStoryDraftUseCase(mock_repo)

        with pytest.raises(ValidationError, match="Story title cannot be empty"):
            UpdateStoryDraftRequest(title="")

        mock_repo.find_by_id.assert_not_called()

    @pytest.mark.asyncio
    async def test_execute_raises_error_on_title_too_long(self):
        """Test that title > 500 chars raises ValidationError at DTO level."""
        mock_repo = AsyncMock()
        use_case = UpdateStoryDraftUseCase(mock_repo)

        long_title = "a" * 501

        with pytest.raises(ValidationError, match="Story title cannot exceed 500 characters"):
            UpdateStoryDraftRequest(title=long_title)

        mock_repo.find_by_id.assert_not_called()

    @pytest.mark.asyncio
    async def test_execute_updates_partial_fields(self):
        """Test updating only some fields leaves others unchanged."""
        mock_repo = AsyncMock()
        draft_id = EntityId.generate()

        existing_draft = StoryDraftEntity(
            id=draft_id,
            title="Original Title",
            description="Original description",
            acceptance_criteria=["Original criterion"],
            project_id=EntityId.generate(),
            created_by=EntityId.generate(),
            status=RefinementStatus.DRAFT,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        mock_repo.find_by_id.return_value = existing_draft
        mock_repo.save.return_value = existing_draft

        use_case = UpdateStoryDraftUseCase(mock_repo)

        request = UpdateStoryDraftRequest(title="Updated Title")
        result = await use_case.execute(
            draft_id=str(draft_id.value),
            request=request,
        )

        assert result is not None
        assert result.title == "Updated Title"
        assert result.description == "Original description"
