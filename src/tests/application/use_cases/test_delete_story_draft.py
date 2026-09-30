"""Tests for DeleteStoryDraftUseCase."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from src.app.features.refinement.application.use_cases.delete_story_draft import DeleteStoryDraftUseCase
from src.app.features.refinement.domain.entities.story_draft_entity import StoryDraftEntity
from src.app.features.refinement.domain.exceptions.refinement_exceptions import (
    StoryDraftAlreadyApprovedError,
    StoryDraftNotFoundError,
)
from src.app.features.refinement.domain.value_objects.draft_status import DraftStatus
from src.app.shared.domain.value_objects.entity_id import EntityId
from src.tests.support.request_context import make_request_context


class TestDeleteStoryDraftUseCase:
    """Test draft deletion behavior."""

    @pytest.mark.asyncio
    async def test_execute_deletes_existing_draft(self):
        """Test that an existing draft is removed via the repository."""
        mock_repo = AsyncMock()
        mock_repo.find_by_id.return_value = StoryDraftEntity(
            id=EntityId.generate(),
            title="Pending draft",
            description="As an Admin, I want to export the backlog.",
            acceptance_criteria=["Export includes approved stories only"],
            project_id=EntityId.generate(),
            created_by=EntityId.generate(),
            status=DraftStatus.DRAFT,
            created_at=datetime.now(tz=UTC),
            updated_at=datetime.now(tz=UTC),
        )
        mock_repo.delete.return_value = True

        draft_id = str(uuid4())
        use_case = DeleteStoryDraftUseCase(mock_repo)

        await use_case.execute(draft_id, ctx=make_request_context(user_id=str(uuid4())))

        mock_repo.delete.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_execute_raises_when_draft_missing(self):
        """Test that deleting an unknown draft raises StoryDraftNotFoundError."""
        mock_repo = AsyncMock()
        mock_repo.find_by_id.return_value = None
        mock_repo.delete.return_value = False

        draft_id = str(uuid4())
        use_case = DeleteStoryDraftUseCase(mock_repo)

        with pytest.raises(StoryDraftNotFoundError):
            await use_case.execute(draft_id, ctx=make_request_context(user_id=str(uuid4())))

    @pytest.mark.asyncio
    async def test_execute_refuses_to_discard_an_approved_draft(self):
        """Test that discarding an applied draft is refused, not silently reported as done."""
        mock_repo = AsyncMock()
        mock_repo.find_by_id.return_value = StoryDraftEntity(
            id=EntityId.generate(),
            title="Already approved",
            description="As an Admin, I want to export the backlog.",
            acceptance_criteria=["Export includes approved stories only"],
            project_id=EntityId.generate(),
            created_by=EntityId.generate(),
            status=DraftStatus.APPLIED,
            created_at=datetime.now(tz=UTC),
            updated_at=datetime.now(tz=UTC),
        )

        use_case = DeleteStoryDraftUseCase(mock_repo)

        with pytest.raises(StoryDraftAlreadyApprovedError):
            await use_case.execute(str(uuid4()), ctx=make_request_context(user_id=str(uuid4())))

        mock_repo.delete.assert_not_called()
