"""Tests for DeleteStoryDraftUseCase."""

from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from src.app.features.refinement.application.use_cases.delete_story_draft import DeleteStoryDraftUseCase
from src.app.features.refinement.domain.exceptions.refinement_exceptions import StoryDraftNotFoundError


class TestDeleteStoryDraftUseCase:
    """Test draft deletion behavior."""

    @pytest.mark.asyncio
    async def test_execute_deletes_existing_draft(self):
        """Test that an existing draft is removed via the repository."""
        mock_repo = AsyncMock()
        mock_repo.delete.return_value = True

        draft_id = str(uuid4())
        use_case = DeleteStoryDraftUseCase(mock_repo)

        await use_case.execute(draft_id, deleted_by=str(uuid4()))

        mock_repo.delete.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_execute_raises_when_draft_missing(self):
        """Test that deleting an unknown draft raises StoryDraftNotFoundError."""
        mock_repo = AsyncMock()
        mock_repo.delete.return_value = False

        draft_id = str(uuid4())
        use_case = DeleteStoryDraftUseCase(mock_repo)

        with pytest.raises(StoryDraftNotFoundError):
            await use_case.execute(draft_id, deleted_by=str(uuid4()))
