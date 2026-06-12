"""
Tests for DeleteStoryUseCase.

Tests story deletion including error handling.
"""

from datetime import UTC, datetime
from unittest.mock import AsyncMock
from uuid import UUID, uuid4

import pytest

from src.app.features.stories.application.use_cases.delete_story import DeleteStoryUseCase
from src.app.features.stories.domain.entities.story_entity import StoryEntity
from src.app.features.stories.domain.exceptions.story_exceptions import StoryNotFoundError
from src.app.features.stories.domain.value_objects.story_priority import StoryPriority
from src.app.features.stories.domain.value_objects.story_status import StoryStatus
from src.app.shared.domain.value_objects.entity_id import EntityId


class TestDeleteStoryUseCase:
    """Test DeleteStoryUseCase functionality."""

    @pytest.mark.asyncio
    async def test_execute_deletes_story_successfully(self):
        """Test successful story deletion."""
        mock_repo = AsyncMock()
        story_id = uuid4()

        existing_entity = StoryEntity(
            id=EntityId.from_string(str(story_id)),
            title="Story",
            description=None,
            project_id=EntityId.generate(),
            created_by=EntityId.generate(),
            assigned_to=None,
            status=StoryStatus.TODO,
            priority=StoryPriority.MEDIUM,
            points=None,
            created_at=datetime.now(tz=UTC),
            updated_at=datetime.now(tz=UTC),
        )
        mock_repo.find_by_id.return_value = existing_entity

        use_case = DeleteStoryUseCase(mock_repo)

        result = await use_case.execute(str(story_id), created_by="test-user")

        assert result is None
        mock_repo.find_by_id.assert_called_once_with(story_id)
        mock_repo.delete.assert_called_once_with(story_id)

    @pytest.mark.asyncio
    async def test_execute_returns_false_when_story_not_found(self):
        """Test that non-existent story raises StoryNotFoundError."""
        mock_repo = AsyncMock()
        mock_repo.find_by_id.return_value = None

        use_case = DeleteStoryUseCase(mock_repo)
        story_id = uuid4()

        with pytest.raises(StoryNotFoundError):
            await use_case.execute(str(story_id), created_by="test-user")

        mock_repo.find_by_id.assert_called_once()
        mock_repo.delete.assert_not_called()

    @pytest.mark.asyncio
    async def test_execute_parses_uuid_string_correctly(self):
        """Test that UUID string is correctly parsed."""
        mock_repo = AsyncMock()
        story_id = uuid4()

        existing_entity = StoryEntity(
            id=EntityId.from_string(str(story_id)),
            title="Story",
            description=None,
            project_id=EntityId.generate(),
            created_by=EntityId.generate(),
            assigned_to=None,
            status=StoryStatus.TODO,
            priority=StoryPriority.MEDIUM,
            points=None,
            created_at=datetime.now(tz=UTC),
            updated_at=datetime.now(tz=UTC),
        )
        mock_repo.find_by_id.return_value = existing_entity

        use_case = DeleteStoryUseCase(mock_repo)

        await use_case.execute(str(story_id), created_by="test-user")

        called_with = mock_repo.find_by_id.call_args[0][0]
        assert called_with == story_id
        assert isinstance(called_with, UUID)

    @pytest.mark.asyncio
    async def test_execute_raises_error_on_invalid_uuid(self):
        """Test that invalid UUID string raises ValueError."""
        # Setup
        mock_repo = AsyncMock()
        use_case = DeleteStoryUseCase(mock_repo)

        # Execute & Assert
        with pytest.raises(ValueError):
            await use_case.execute("not-a-valid-uuid", created_by="test-user")

        mock_repo.delete.assert_not_called()
