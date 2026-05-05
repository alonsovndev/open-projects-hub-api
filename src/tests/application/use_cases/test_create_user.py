"""
Tests for CreateUserUseCase.

Tests user creation including password hashing and duplicate handling.
"""
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock

from src.app.features.application.dtos.user_dto import UserCreateRequest, UserResponse
from src.app.features.application.exceptions.user_exception import UserAlreadyExistsException
from src.app.features.application.use_cases.create_user import CreateUserUseCase
from src.app.features.domain.entities.user_entity import UserEntity
from src.app.features.domain.value_objects.email import Email
from src.app.features.domain.value_objects.user_role import UserRole
from src.app.shared.domain.value_objects.entity_id import EntityId


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
            first_name="New",
            last_name="User",
            password_hash="hashed_password",
            role=UserRole.USER
        )
        mock_repo.save.return_value = created_entity
        
        use_case = CreateUserUseCase(mock_repo)
        
        payload = UserCreateRequest(
            first_name="New",
            last_name="User",
            email="newuser@example.com",
            password="SecurePass123"
        )
        
        # Execute
        result = await use_case.execute(payload)
        
        # Assert
        assert isinstance(result, UserResponse)
        assert result.email == "newuser@example.com"
        assert result.fullname == "New User"
        mock_repo.find_by_email.assert_called_once()
        mock_repo.save.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_raises_error_when_user_exists(self):
        """Test that creating duplicate user raises error."""
        # Setup
        existing_user = UserEntity(
            id=EntityId.generate(),
            email=Email("existing@example.com"),
            first_name="Existing",
            last_name="User",
            password_hash="hashed",
            role=UserRole.USER
        )
        
        mock_repo = AsyncMock()
        mock_repo.find_by_email.return_value = existing_user
        
        use_case = CreateUserUseCase(mock_repo)
        
        payload = UserCreateRequest(
            first_name="New",
            last_name="User",
            email="existing@example.com",
            password="SecurePass123"
        )
        
        # Execute & Assert
        with pytest.raises(UserAlreadyExistsException) as exc_info:
            await use_case.execute(payload)
        
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
        
        use_case = CreateUserUseCase(mock_repo)
        
        payload = UserCreateRequest(
            first_name="New",
            last_name="User",
            email="raceuser@example.com",
            password="SecurePass123"
        )
        
        # Execute & Assert
        with pytest.raises(UserAlreadyExistsException) as exc_info:
            await use_case.execute(payload)
        
        assert "raceuser@example.com" in str(exc_info.value)
        mock_repo.save.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_hashes_password(self):
        """Test that password is hashed before saving."""
        # Setup
        mock_repo = AsyncMock()
        mock_repo.find_by_email.return_value = None
        
        created_entity = UserEntity(
            id=EntityId.generate(),
            email=Email("user@example.com"),
            first_name="Test",
            last_name="User",
            password_hash="$2b$12$hashed_password_here",
            role=UserRole.USER
        )
        mock_repo.save.return_value = created_entity
        
        use_case = CreateUserUseCase(mock_repo)
        
        payload = UserCreateRequest(
            first_name="Test",
            last_name="User",
            email="user@example.com",
            password="PlainPassword123"
        )
        
        # Execute
        await use_case.execute(payload)
        
        # Assert - check that save was called with hashed password
        save_call_args = mock_repo.save.call_args[0][0]
        assert save_call_args.password_hash != "PlainPassword123"
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
            first_name="Test",
            last_name="User",
            password_hash="hashed",
            role=UserRole.USER
        )
        mock_repo.save.return_value = created_entity
        
        use_case = CreateUserUseCase(mock_repo)
        
        payload = UserCreateRequest(
            first_name="Test",
            last_name="User",
            email="User@Example.COM",  # Mixed case
            password="SecurePass123"
        )
        
        # Execute
        result = await use_case.execute(payload)
        
        # Assert
        assert result.email == "user@example.com"
