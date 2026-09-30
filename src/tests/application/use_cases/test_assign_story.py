"""
Tests for AssignStoryUseCase.

Tests story assignment including validation and error handling.
"""

from datetime import UTC, datetime
from unittest.mock import AsyncMock
from uuid import UUID, uuid4

import pytest

from src.app.features.stories.application.dtos.story_dto import StoryResponse
from src.app.features.stories.application.use_cases.assign_story import AssignStoryUseCase
from src.app.features.stories.domain.entities.story_entity import StoryEntity
from src.app.features.stories.domain.exceptions.story_exceptions import StoryNotFoundError
from src.app.features.stories.domain.value_objects.story_priority import StoryPriority
from src.app.features.stories.domain.value_objects.story_status import StoryStatus
from src.app.features.user.domain.entities.user_entity import UserEntity
from src.app.features.user.domain.value_objects.user_role import UserRole
from src.app.shared.domain.exceptions.domain_exceptions import NotFoundError
from src.app.shared.domain.value_objects.email import Email
from src.app.shared.domain.value_objects.entity_id import EntityId
from src.tests.support.request_context import TEST_WORKSPACE_ID, TEST_WORKSPACE_UUID, make_request_context


def teammate_repository(workspace_id: str = TEST_WORKSPACE_ID) -> AsyncMock:
    """A user repository whose every user belongs to the given workspace."""
    user_repository = AsyncMock()
    user_repository.find_by_id.side_effect = lambda user_id: UserEntity(
        id=user_id,
        email=Email("teammate@example.com"),
        display_name="Teammate",
        password_hash="hash",
        role=UserRole.MEMBER,
        workspace_id=EntityId.from_string(workspace_id),
    )
    return user_repository


class TestAssignStoryUseCase:
    """Test AssignStoryUseCase functionality."""

    @pytest.mark.asyncio
    async def test_execute_assigns_story_to_user(self):
        """Test successful story assignment."""
        # Setup
        mock_repo = AsyncMock()
        story_id = uuid4()
        user_id = EntityId.generate()

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
        mock_repo.save.return_value = existing_entity

        use_case = AssignStoryUseCase(mock_repo, teammate_repository())

        # Execute
        result = await use_case.execute(
            story_id=str(story_id),
            user_id=str(user_id.value),
            ctx=make_request_context(),
        )

        assert isinstance(result, StoryResponse)
        assert result.assigned_to == str(user_id.value)
        assert existing_entity.assigned_to == user_id
        mock_repo.find_by_id.assert_called_once_with(story_id, workspace_id=TEST_WORKSPACE_UUID)
        mock_repo.save.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_reassigns_already_assigned_story(self):
        """Test reassigning a story to a different user."""
        # Setup
        mock_repo = AsyncMock()
        story_id = uuid4()
        old_user = EntityId.generate()
        new_user = EntityId.generate()

        existing_entity = StoryEntity(
            id=EntityId.from_string(str(story_id)),
            title="Story",
            description=None,
            project_id=EntityId.generate(),
            created_by=EntityId.generate(),
            assigned_to=old_user,
            status=StoryStatus.IN_PROGRESS,
            priority=StoryPriority.HIGH,
            points=5,
            created_at=datetime.now(tz=UTC),
            updated_at=datetime.now(tz=UTC),
        )
        mock_repo.find_by_id.return_value = existing_entity
        mock_repo.save.return_value = existing_entity

        use_case = AssignStoryUseCase(mock_repo, teammate_repository())

        # Execute
        result = await use_case.execute(
            story_id=str(story_id),
            user_id=str(new_user.value),
            ctx=make_request_context(),
        )

        # Assert
        assert result.assigned_to == str(new_user.value)
        assert existing_entity.assigned_to == new_user

    @pytest.mark.asyncio
    async def test_execute_returns_none_when_story_not_found(self):
        """Test that non-existent story raises StoryNotFoundError."""
        # Setup
        mock_repo = AsyncMock()
        mock_repo.find_by_id.return_value = None

        use_case = AssignStoryUseCase(mock_repo, teammate_repository())

        # Execute & Assert
        with pytest.raises(StoryNotFoundError):
            await use_case.execute(
                story_id=str(uuid4()),
                user_id=str(uuid4()),
                ctx=make_request_context(),
            )
        mock_repo.find_by_id.assert_called_once()
        mock_repo.save.assert_not_called()

    @pytest.mark.asyncio
    async def test_execute_raises_error_when_save_fails(self):
        """Test that successful save returns the expected entity."""
        # Setup
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
        mock_repo.save.return_value = existing_entity

        use_case = AssignStoryUseCase(mock_repo, teammate_repository())

        # Execute
        result = await use_case.execute(
            story_id=str(story_id),
            user_id=str(uuid4()),
            ctx=make_request_context(),
        )

        assert isinstance(result, StoryResponse)
        mock_repo.save.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_parses_user_id_correctly(self):
        """Test that user_id string is correctly parsed to EntityId."""
        # Setup
        mock_repo = AsyncMock()
        story_id = uuid4()
        user_id = uuid4()

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
        mock_repo.save.return_value = existing_entity

        use_case = AssignStoryUseCase(mock_repo, teammate_repository())

        # Execute
        await use_case.execute(
            story_id=str(story_id),
            user_id=str(user_id),
            ctx=make_request_context(),
        )

        # Assert
        assert existing_entity.assigned_to.value == user_id

    @pytest.mark.asyncio
    async def test_execute_raises_error_on_invalid_user_uuid(self):
        """Test that invalid user UUID raises ValueError."""
        # Setup
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

        use_case = AssignStoryUseCase(mock_repo, teammate_repository())

        # Execute & Assert
        with pytest.raises(ValueError):
            await use_case.execute(
                story_id=str(story_id),
                user_id="not-a-valid-uuid",
                ctx=make_request_context(),
            )


class TestAssignStoryWorkspaceBoundary:
    @pytest.mark.asyncio
    async def test_execute_refuses_an_assignee_from_another_workspace(self):
        """A foreign user id answers exactly like an unknown one, so it cannot be probed."""
        story_repository = AsyncMock()
        story_repository.find_by_id.return_value = StoryEntity(
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
        other_workspace = str(uuid4())
        use_case = AssignStoryUseCase(story_repository, teammate_repository(other_workspace))

        with pytest.raises(NotFoundError):
            await use_case.execute(story_id=str(uuid4()), user_id=str(uuid4()), ctx=make_request_context())

        story_repository.save.assert_not_called()

    @pytest.mark.asyncio
    async def test_execute_looks_the_story_up_in_the_callers_workspace(self):
        story_repository = AsyncMock()
        story_repository.find_by_id.return_value = None
        use_case = AssignStoryUseCase(story_repository, teammate_repository())
        story_id = uuid4()

        with pytest.raises(StoryNotFoundError):
            await use_case.execute(story_id=str(story_id), user_id=str(uuid4()), ctx=make_request_context())

        story_repository.find_by_id.assert_awaited_once_with(story_id, workspace_id=UUID(TEST_WORKSPACE_ID))
