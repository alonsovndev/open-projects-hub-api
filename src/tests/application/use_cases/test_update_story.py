"""
Tests for UpdateStoryUseCase.

Tests story update including validation and error handling.
"""

from datetime import datetime, timezone
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from pydantic import ValidationError

from src.app.features.stories.application.dtos.story_dto import StoryResponse, UpdateStoryRequest
from src.app.features.stories.application.use_cases.update_story import UpdateStoryUseCase
from src.app.features.stories.domain.entities.story_entity import StoryEntity
from src.app.features.stories.domain.value_objects.story_priority import StoryPriority
from src.app.features.stories.domain.value_objects.story_status import StoryStatus
from src.app.shared.domain.value_objects.entity_id import EntityId


class TestUpdateStoryUseCase:
    """Test UpdateStoryUseCase functionality."""

    @pytest.mark.asyncio
    async def test_execute_updates_story_title(self):
        """Test updating story title."""
        mock_repo = AsyncMock()
        story_id = uuid4()

        existing_entity = StoryEntity(
            id=EntityId.from_string(str(story_id)),
            title="Old Title",
            description="Description",
            project_id=EntityId.generate(),
            created_by=EntityId.generate(),
            assigned_to=None,
            status=StoryStatus.TODO,
            priority=StoryPriority.MEDIUM,
            points=None,
            created_at=datetime.now(tz=timezone.utc),
            updated_at=datetime.now(tz=timezone.utc),
        )
        mock_repo.find_by_id.return_value = existing_entity
        mock_repo.save.return_value = existing_entity

        use_case = UpdateStoryUseCase(mock_repo)

        request = UpdateStoryRequest(title="New Title")
        result = await use_case.execute(
            story_id=str(story_id),
            request=request,
            created_by="test-user",
        )

        assert isinstance(result, StoryResponse)
        assert result.title == "New Title"
        mock_repo.find_by_id.assert_called_once_with(story_id)
        mock_repo.save.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_updates_multiple_fields(self):
        """Test updating multiple story fields at once."""
        mock_repo = AsyncMock()
        story_id = uuid4()

        existing_entity = StoryEntity(
            id=EntityId.from_string(str(story_id)),
            title="Old Title",
            description="Old Description",
            project_id=EntityId.generate(),
            created_by=EntityId.generate(),
            assigned_to=None,
            status=StoryStatus.TODO,
            priority=StoryPriority.LOW,
            points=None,
            created_at=datetime.now(tz=timezone.utc),
            updated_at=datetime.now(tz=timezone.utc),
        )
        mock_repo.find_by_id.return_value = existing_entity
        mock_repo.save.return_value = existing_entity

        use_case = UpdateStoryUseCase(mock_repo)

        request = UpdateStoryRequest(
            title="New Title",
            description="New Description",
            status="in_progress",
            priority="high",
            points=8,
        )
        result = await use_case.execute(
            story_id=str(story_id),
            request=request,
            created_by="test-user",
        )

        assert result.title == "New Title"
        assert result.description == "New Description"
        assert result.status == "in_progress"
        assert result.priority == "high"
        assert result.points == 8

    @pytest.mark.asyncio
    async def test_execute_returns_none_when_story_not_found(self):
        """Test that non-existent story returns None."""
        mock_repo = AsyncMock()
        mock_repo.find_by_id.return_value = None

        use_case = UpdateStoryUseCase(mock_repo)

        request = UpdateStoryRequest(title="New Title")
        result = await use_case.execute(
            story_id=str(uuid4()),
            request=request,
            created_by="test-user",
        )

        assert result is None
        mock_repo.find_by_id.assert_called_once()
        mock_repo.save.assert_not_called()

    @pytest.mark.asyncio
    async def test_execute_raises_error_on_invalid_status(self):
        """Test that invalid status raises ValidationError at DTO level."""
        with pytest.raises(ValidationError, match="Status must be one of"):
            UpdateStoryRequest(status="invalid_status")

    @pytest.mark.asyncio
    async def test_execute_raises_error_on_invalid_priority(self):
        """Test that invalid priority raises ValidationError at DTO level."""
        with pytest.raises(ValidationError, match="Priority must be one of"):
            UpdateStoryRequest(priority="invalid_priority")

    @pytest.mark.asyncio
    async def test_execute_accepts_valid_statuses(self):
        """Test that all valid statuses are accepted."""
        for status_str, status_enum in [
            ("todo", StoryStatus.TODO),
            ("in_progress", StoryStatus.IN_PROGRESS),
            ("done", StoryStatus.DONE),
        ]:
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
                created_at=datetime.now(tz=timezone.utc),
                updated_at=datetime.now(tz=timezone.utc),
            )
            mock_repo.find_by_id.return_value = existing_entity
            mock_repo.save.return_value = existing_entity

            use_case = UpdateStoryUseCase(mock_repo)

            request = UpdateStoryRequest(status=status_str)
            result = await use_case.execute(
                story_id=str(story_id),
                request=request,
                created_by="test-user",
            )

            assert result.status == status_str
            assert existing_entity.status == status_enum

    @pytest.mark.asyncio
    async def test_execute_raises_error_when_save_fails(self):
        """Test that save failure raises ValueError."""
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
            created_at=datetime.now(tz=timezone.utc),
            updated_at=datetime.now(tz=timezone.utc),
        )
        mock_repo.find_by_id.return_value = existing_entity
        mock_repo.save.return_value = None

        use_case = UpdateStoryUseCase(mock_repo)

        request = UpdateStoryRequest(title="New Title")
        with pytest.raises(ValueError, match="Failed to update story"):
            await use_case.execute(
                story_id=str(story_id),
                request=request,
                created_by="test-user",
            )

    @pytest.mark.asyncio
    async def test_execute_validates_points(self):
        """Test that points validation works at DTO level."""
        with pytest.raises(ValidationError, match="Story points cannot be negative"):
            UpdateStoryRequest(points=-1)

        with pytest.raises(ValidationError, match="Story points cannot exceed 100"):
            UpdateStoryRequest(points=101)
