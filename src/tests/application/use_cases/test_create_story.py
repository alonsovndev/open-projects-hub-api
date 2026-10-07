"""
Tests for CreateStoryUseCase.

Tests story creation including validation and error handling.
"""

from datetime import UTC, datetime
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from src.app.features.stories.application.dtos.story_dto import CreateStoryRequest, StoryResponse
from src.app.features.stories.application.use_cases.create_story import CreateStoryUseCase
from src.app.features.stories.domain.entities.story_entity import StoryEntity
from src.app.features.stories.domain.value_objects.story_priority import StoryPriority
from src.app.features.stories.domain.value_objects.story_status import StoryStatus
from src.app.shared.domain.exceptions.domain_exceptions import NotFoundError, ValidationError
from src.app.shared.domain.value_objects.entity_id import EntityId
from src.tests.support.request_context import TEST_WORKSPACE_UUID, make_request_context


def visible_projects(exists: bool = True) -> AsyncMock:
    """A project repository that reports the target project as in (or out of) the caller's workspace."""
    project_repository = AsyncMock()
    project_repository.exists.return_value = exists
    return project_repository


class TestCreateStoryUseCase:
    """Test CreateStoryUseCase functionality."""

    @pytest.mark.asyncio
    async def test_execute_creates_story_successfully(self):
        """Test successful story creation with minimal fields."""
        mock_repo = AsyncMock()
        project_id = EntityId.generate()
        created_by = EntityId.generate()

        created_entity = StoryEntity(
            id=EntityId.generate(),
            title="New Story",
            description=None,
            project_id=project_id,
            created_by=created_by,
            assigned_to=None,
            status=StoryStatus.TODO,
            priority=StoryPriority.MEDIUM,
            points=None,
            created_at=datetime.now(tz=UTC),
            updated_at=datetime.now(tz=UTC),
        )
        mock_repo.save.return_value = created_entity

        use_case = CreateStoryUseCase(mock_repo, visible_projects())

        request = CreateStoryRequest(
            title="New Story",
            project_id=str(project_id.value),
        )
        result = await use_case.execute(
            request=request,
            ctx=make_request_context(user_id=str(created_by.value)),
        )

        assert isinstance(result, StoryResponse)
        assert result.title == "New Story"
        assert result.status == "todo"
        assert result.priority == "medium"
        mock_repo.save.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_creates_story_with_all_fields(self):
        """Test story creation with all optional fields."""
        mock_repo = AsyncMock()
        project_id = EntityId.generate()
        created_by = EntityId.generate()

        created_entity = StoryEntity(
            id=EntityId.generate(),
            title="Full Story",
            description="Complete description",
            project_id=project_id,
            created_by=created_by,
            assigned_to=None,
            status=StoryStatus.TODO,
            priority=StoryPriority.HIGH,
            points=5,
            created_at=datetime.now(tz=UTC),
            updated_at=datetime.now(tz=UTC),
        )
        mock_repo.save.return_value = created_entity

        use_case = CreateStoryUseCase(mock_repo, visible_projects())

        request = CreateStoryRequest(
            title="Full Story",
            project_id=str(project_id.value),
            description="Complete description",
            priority="high",
            points=5,
        )
        result = await use_case.execute(
            request=request,
            ctx=make_request_context(user_id=str(created_by.value)),
        )

        assert isinstance(result, StoryResponse)
        assert result.title == "Full Story"
        assert result.description == "Complete description"
        assert result.priority == "high"
        assert result.points == 5

    @pytest.mark.asyncio
    async def test_execute_raises_error_on_empty_title(self):
        """Test that empty title raises ValidationError at DTO level."""
        mock_repo = AsyncMock()

        with pytest.raises(ValidationError, match="Story title cannot be empty"):
            CreateStoryRequest(
                title="",
                project_id=str(uuid4()),
            )

        mock_repo.save.assert_not_called()

    @pytest.mark.asyncio
    async def test_execute_raises_error_on_invalid_priority(self):
        """Test that invalid priority raises ValidationError at DTO level."""
        mock_repo = AsyncMock()

        with pytest.raises(ValidationError, match="Priority must be one of"):
            CreateStoryRequest(
                title="Story",
                project_id=str(uuid4()),
                priority="invalid",
            )

        mock_repo.save.assert_not_called()

    @pytest.mark.asyncio
    async def test_execute_accepts_valid_priorities(self):
        """Test that all valid priorities are accepted."""
        mock_repo = AsyncMock()

        for priority_str, priority_enum in [
            ("low", StoryPriority.LOW),
            ("medium", StoryPriority.MEDIUM),
            ("high", StoryPriority.HIGH),
        ]:
            created_entity = StoryEntity(
                id=EntityId.generate(),
                title="Story",
                description=None,
                project_id=EntityId.generate(),
                created_by=EntityId.generate(),
                assigned_to=None,
                status=StoryStatus.TODO,
                priority=priority_enum,
                points=None,
                created_at=datetime.now(tz=UTC),
                updated_at=datetime.now(tz=UTC),
            )
            mock_repo.save.return_value = created_entity

            use_case = CreateStoryUseCase(mock_repo, visible_projects())

            request = CreateStoryRequest(
                title="Story",
                project_id=str(uuid4()),
                priority=priority_str,
            )
            result = await use_case.execute(
                request=request,
                ctx=make_request_context(user_id=str(uuid4())),
            )

            assert result.priority == priority_str

    @pytest.mark.asyncio
    async def test_execute_raises_error_when_save_fails(self):
        """Test that save returns expected entity."""
        mock_repo = AsyncMock()

        created_entity = StoryEntity(
            id=EntityId.generate(),
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
        mock_repo.save.return_value = created_entity

        use_case = CreateStoryUseCase(mock_repo, visible_projects())

        request = CreateStoryRequest(
            title="Story",
            project_id=str(uuid4()),
        )
        result = await use_case.execute(
            request=request,
            ctx=make_request_context(user_id=str(uuid4())),
        )

        assert isinstance(result, StoryResponse)
        mock_repo.save.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_validates_points(self):
        """Test that points validation works at DTO level."""
        with pytest.raises(ValidationError, match="Story points cannot be negative"):
            CreateStoryRequest(
                title="Story",
                project_id=str(uuid4()),
                points=-1,
            )

        with pytest.raises(ValidationError, match="Story points cannot exceed 100"):
            CreateStoryRequest(
                title="Story",
                project_id=str(uuid4()),
                points=101,
            )


class TestCreateStoryWorkspaceBoundary:
    @pytest.mark.asyncio
    async def test_a_project_of_another_workspace_is_not_found(self):
        story_repository = AsyncMock()
        projects = visible_projects(exists=False)
        use_case = CreateStoryUseCase(story_repository, projects)
        project_id = uuid4()

        with pytest.raises(NotFoundError):
            await use_case.execute(
                CreateStoryRequest(title="Story", project_id=str(project_id)), ctx=make_request_context()
            )

        projects.exists.assert_awaited_once_with(project_id, workspace_id=TEST_WORKSPACE_UUID)
        story_repository.save.assert_not_called()
