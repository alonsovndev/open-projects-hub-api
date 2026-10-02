"""
Tests for CreateUserUseCase.

Tests user creation including password hashing and duplicate handling.
"""

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock

import pytest
from pydantic import ValidationError as PydanticValidationError

from src.app.features.auth.application.services.email_links import EmailLinks
from src.app.features.user.application.dtos.user_dto import UserCreateRequest, UserResponse
from src.app.features.user.application.use_cases.create_user import CreateUserUseCase
from src.app.features.user.domain.entities.user_entity import UserEntity
from src.app.features.user.domain.exceptions.user_exceptions import UserAlreadyExistsError
from src.app.features.user.domain.value_objects.user_role import UserRole
from src.app.features.workspaces.domain.exceptions.workspace_exceptions import WorkspaceUserLimitExceededError
from src.app.shared.domain.value_objects.email import Email
from src.app.shared.domain.value_objects.entity_id import EntityId
from src.tests.support.request_context import TEST_WORKSPACE_UUID, make_request_context


class TestCreateUserUseCase:
    """Test CreateUserUseCase functionality."""

    @pytest.mark.asyncio
    async def test_execute_creates_user_successfully(self):
        """Test successful user creation."""
        # Setup
        mock_repo = AsyncMock()
        mock_repo.find_by_email.return_value = None  # No existing user

        created_entity = UserEntity(
            id=EntityId.generate(),
            email=Email("newuser@example.com"),
            display_name="New User",
            password_hash="hashed_password",
            role=UserRole.VIEWER,
        )
        mock_repo.save.return_value = created_entity

        mock_repo.count_by_workspace.return_value = 1
        use_case = CreateUserUseCase(mock_repo, AsyncMock(), AsyncMock(), EmailLinks("http://localhost:5173"), 5)

        payload = UserCreateRequest(display_name="New User", email="newuser@example.com")

        # Execute
        result = await use_case.execute(payload, ctx=make_request_context())

        # Assert
        assert isinstance(result, UserResponse)
        assert result.email == "newuser@example.com"
        assert result.display_name == "New User"
        mock_repo.find_by_email.assert_called_once()
        mock_repo.save.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_raises_error_when_user_exists(self):
        """Test that creating duplicate user raises error."""
        # Setup
        existing_user = UserEntity(
            id=EntityId.generate(),
            email=Email("existing@example.com"),
            display_name="Existing User",
            password_hash="hashed",
            role=UserRole.VIEWER,
        )

        mock_repo = AsyncMock()
        mock_repo.find_by_email.return_value = existing_user

        mock_repo.count_by_workspace.return_value = 1
        use_case = CreateUserUseCase(mock_repo, AsyncMock(), AsyncMock(), EmailLinks("http://localhost:5173"), 5)

        payload = UserCreateRequest(display_name="New User", email="existing@example.com")

        # Execute & Assert
        with pytest.raises(UserAlreadyExistsError) as exc_info:
            await use_case.execute(payload, ctx=make_request_context())

        assert "existing@example.com" in str(exc_info.value)
        mock_repo.find_by_email.assert_called_once()
        mock_repo.save.assert_not_called()

    @pytest.mark.asyncio
    async def test_execute_handles_race_condition(self):
        """Test that race condition (repository returns None) raises error."""
        # Setup - simulate race condition where user is created between check and save
        mock_repo = AsyncMock()
        mock_repo.find_by_email.return_value = None  # User doesn't exist during check
        mock_repo.save.return_value = None  # But returns None due to duplicate (race condition)

        mock_repo.count_by_workspace.return_value = 1
        use_case = CreateUserUseCase(mock_repo, AsyncMock(), AsyncMock(), EmailLinks("http://localhost:5173"), 5)

        payload = UserCreateRequest(display_name="Race User", email="raceuser@example.com")

        # Execute & Assert
        with pytest.raises(UserAlreadyExistsError) as exc_info:
            await use_case.execute(payload, ctx=make_request_context())

        assert "raceuser@example.com" in str(exc_info.value)
        mock_repo.save.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_stores_a_hashed_placeholder_password(self):
        """The invitee picks their own password later; until then the hash is of a random value."""
        # Setup
        mock_repo = AsyncMock()
        mock_repo.find_by_email.return_value = None

        created_entity = UserEntity(
            id=EntityId.generate(),
            email=Email("user@example.com"),
            display_name="Test User",
            password_hash="$2b$12$hashed_password_here",
            role=UserRole.VIEWER,
        )
        mock_repo.save.return_value = created_entity

        mock_repo.count_by_workspace.return_value = 1
        use_case = CreateUserUseCase(mock_repo, AsyncMock(), AsyncMock(), EmailLinks("http://localhost:5173"), 5)

        payload = UserCreateRequest(display_name="Test User", email="user@example.com")

        # Execute
        await use_case.execute(payload, ctx=make_request_context())

        # Assert - check that save was called with hashed password
        save_call_args = mock_repo.save.call_args[0][0]
        assert save_call_args.password_hash.startswith("$2b$")  # bcrypt format

    @pytest.mark.asyncio
    async def test_execute_converts_email_to_lowercase(self):
        """Test that email is converted to lowercase."""
        # Setup
        mock_repo = AsyncMock()
        mock_repo.find_by_email.return_value = None

        created_entity = UserEntity(
            id=EntityId.generate(),
            email=Email("user@example.com"),
            display_name="Test User",
            password_hash="hashed",
            role=UserRole.VIEWER,
        )
        mock_repo.save.return_value = created_entity

        mock_repo.count_by_workspace.return_value = 1
        use_case = CreateUserUseCase(mock_repo, AsyncMock(), AsyncMock(), EmailLinks("http://localhost:5173"), 5)

        payload = UserCreateRequest(
            display_name="Test User",
            email="User@Example.COM",  # Mixed case
        )

        # Execute
        result = await use_case.execute(payload, ctx=make_request_context())

        # Assert
        assert result.email == "user@example.com"


class TestCreateWorkspaceMember:
    @pytest.mark.asyncio
    async def test_the_new_user_joins_the_admins_workspace_unverified_and_without_credits(self):
        """An Admin's word does not prove the address: the person must verify it themselves."""
        user_repository = AsyncMock()
        user_repository.find_by_email.return_value = None
        user_repository.save.side_effect = lambda user_entity: user_entity
        user_repository.count_by_workspace.return_value = 1
        use_case = CreateUserUseCase(user_repository, AsyncMock(), AsyncMock(), EmailLinks("http://localhost:5173"), 5)

        await use_case.execute(
            UserCreateRequest(display_name="Teammate", email="mate@example.com"),
            ctx=make_request_context(),
        )

        created = user_repository.save.call_args[0][0]
        assert created.role is UserRole.MEMBER
        assert created.workspace_id.value == TEST_WORKSPACE_UUID
        assert created.is_email_verified is False
        assert created.ai_credits_remaining == 0
        assert created.ai_credits_granted == 0

    @pytest.mark.asyncio
    async def test_a_viewer_can_be_created(self):
        user_repository = AsyncMock()
        user_repository.find_by_email.return_value = None
        user_repository.save.side_effect = lambda user_entity: user_entity
        user_repository.count_by_workspace.return_value = 1
        use_case = CreateUserUseCase(user_repository, AsyncMock(), AsyncMock(), EmailLinks("http://localhost:5173"), 5)

        await use_case.execute(
            UserCreateRequest(display_name="Client", email="client@example.com", role="viewer"),
            ctx=make_request_context(),
        )

        assert user_repository.save.call_args[0][0].role is UserRole.VIEWER

    def test_an_admin_role_is_refused(self):
        """No second Admin until roles can be changed and accounts removed."""
        with pytest.raises(PydanticValidationError):
            UserCreateRequest(display_name="Boss", email="boss@example.com", role="admin")

    @pytest.mark.asyncio
    async def test_the_new_user_is_emailed_a_verification_code(self):
        user_repository = AsyncMock()
        user_repository.find_by_email.return_value = None
        user_repository.save.side_effect = lambda user_entity: user_entity
        verification_code_repository, email_sender = AsyncMock(), AsyncMock()
        user_repository.count_by_workspace.return_value = 1
        use_case = CreateUserUseCase(
            user_repository, verification_code_repository, email_sender, EmailLinks("http://localhost:5173"), 5
        )

        await use_case.execute(
            UserCreateRequest(display_name="Teammate", email="mate@example.com"),
            ctx=make_request_context(),
        )

        verification_code_repository.create.assert_awaited_once()
        assert email_sender.send.call_args.kwargs["to"] == "mate@example.com"

    @pytest.mark.asyncio
    async def test_the_invite_email_links_to_verification_and_lasts_a_day(self):
        user_repository = AsyncMock()
        user_repository.find_by_email.return_value = None
        user_repository.save.side_effect = lambda user_entity: user_entity
        verification_code_repository, email_sender = AsyncMock(), AsyncMock()
        user_repository.count_by_workspace.return_value = 1
        use_case = CreateUserUseCase(
            user_repository, verification_code_repository, email_sender, EmailLinks("http://localhost:5173"), 5
        )

        await use_case.execute(
            UserCreateRequest(display_name="Teammate", email="mate@example.com"),
            ctx=make_request_context(),
        )

        stored_code = verification_code_repository.create.call_args[0][0]
        remaining = stored_code.expires_at - datetime.now(UTC)
        assert timedelta(hours=23) < remaining <= timedelta(hours=24)
        body = email_sender.send.call_args.kwargs["body"]
        assert "http://localhost:5173/verify-email?email=mate%40example.com&code=" in body
        assert "setPassword=1" in body
        assert "24 hours" in body


class TestWorkspaceUserLimit:
    @pytest.mark.asyncio
    @pytest.mark.parametrize("existing_users", [5, 6])
    async def test_adding_a_user_at_the_cap_is_refused(self, existing_users):
        user_repository = AsyncMock()
        user_repository.count_by_workspace.return_value = existing_users
        use_case = CreateUserUseCase(user_repository, AsyncMock(), AsyncMock(), EmailLinks("http://localhost:5173"), 5)

        with pytest.raises(WorkspaceUserLimitExceededError):
            await use_case.execute(
                UserCreateRequest(display_name="Sixth", email="sixth@example.com"), ctx=make_request_context()
            )

        user_repository.save.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_the_count_covers_the_callers_workspace(self):
        user_repository = AsyncMock()
        user_repository.count_by_workspace.return_value = 4
        user_repository.find_by_email.return_value = None
        user_repository.save.side_effect = lambda user_entity: user_entity
        use_case = CreateUserUseCase(user_repository, AsyncMock(), AsyncMock(), EmailLinks("http://localhost:5173"), 5)
        ctx = make_request_context()

        await use_case.execute(UserCreateRequest(display_name="Fifth", email="fifth@example.com"), ctx=ctx)

        user_repository.count_by_workspace.assert_awaited_once_with(ctx.workspace_id)
