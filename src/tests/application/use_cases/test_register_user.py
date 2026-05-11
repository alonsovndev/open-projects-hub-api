"""
Tests for RegisterUserUseCase.

Following API spec:
- POST /auth/register creates user and returns JWT token (auto-login)
- Default role: viewer
- Returns AdminLoginResponse (same as login)
"""
import pytest
from unittest.mock import AsyncMock

from src.app.features.user.application.dtos.auth_dto import AdminLoginResponse
from src.app.features.user.application.dtos.user_dto import UserCreateRequest
from src.app.features.user.application.exceptions.user_exception import UserAlreadyExistsException
from src.app.features.user.application.use_cases.register_user import RegisterUserUseCase
from src.app.features.user.domain.entities.user_entity import UserEntity
from src.app.features.user.domain.value_objects.email import Email
from src.app.features.user.domain.value_objects.user_role import UserRole
from src.app.shared.domain.value_objects.entity_id import EntityId
from src.app.shared.infrastructure.security.jwt_handler import JWTHandler


@pytest.fixture
def jwt_handler():
    return JWTHandler(
        secret_key="test-secret-key-that-is-at-least-32-characters-long",
        expiration_minutes=60,
        validate_secret=False
    )


class TestRegisterUserUseCase:
    """Test RegisterUserUseCase functionality."""

    @pytest.mark.asyncio
    async def test_execute_creates_user_with_viewer_role(self, jwt_handler):
        """Test that registration creates user with default viewer role."""
        mock_repo = AsyncMock()
        mock_repo.find_by_email.return_value = None
        
        created_entity = UserEntity(
            id=EntityId.generate(),
            email=Email("newuser@example.com"),
            display_name="New User",
            password_hash="hashed_password",
            role=UserRole.VIEWER
        )
        mock_repo.save.return_value = created_entity
        
        use_case = RegisterUserUseCase(mock_repo, jwt_handler)
        
        payload = UserCreateRequest(
            display_name="New User",
            email="newuser@example.com",
            password="SecurePass123"
        )
        
        result = await use_case.execute(payload)
        
        assert isinstance(result, AdminLoginResponse)
        assert result.email == "newuser@example.com"
        assert result.display_name == "New User"
        assert result.role == "viewer"
        assert result.token is not None
        assert result.access_token == result.token
        mock_repo.save.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_returns_jwt_token(self, jwt_handler):
        """Test that registration returns valid JWT token (auto-login)."""
        mock_repo = AsyncMock()
        mock_repo.find_by_email.return_value = None
        
        created_entity = UserEntity(
            id=EntityId.generate(),
            email=Email("user@example.com"),
            display_name="Test User",
            password_hash="hashed",
            role=UserRole.VIEWER
        )
        mock_repo.save.return_value = created_entity
        
        use_case = RegisterUserUseCase(mock_repo, jwt_handler)
        
        payload = UserCreateRequest(
            display_name="Test User",
            email="user@example.com",
            password="Password123"
        )
        
        result = await use_case.execute(payload)
        
        assert result.token is not None
        assert len(result.token) > 20  # JWT tokens are long
        assert result.user.email == "user@example.com"
        assert result.user.role == "viewer"

    @pytest.mark.asyncio
    async def test_execute_raises_error_when_email_exists(self, jwt_handler):
        """Test that duplicate email raises UserAlreadyExistsException."""
        existing_user = UserEntity(
            id=EntityId.generate(),
            email=Email("existing@example.com"),
            display_name="Existing User",
            password_hash="hashed",
            role=UserRole.VIEWER
        )
        
        mock_repo = AsyncMock()
        mock_repo.find_by_email.return_value = existing_user
        
        use_case = RegisterUserUseCase(mock_repo, jwt_handler)
        
        payload = UserCreateRequest(
            display_name="New User",
            email="existing@example.com",
            password="SecurePass123"
        )
        
        with pytest.raises(UserAlreadyExistsException) as exc_info:
            await use_case.execute(payload)
        
        assert "existing@example.com" in str(exc_info.value)
        mock_repo.save.assert_not_called()

    @pytest.mark.asyncio
    async def test_execute_hashes_password_before_storing(self, jwt_handler):
        """Test that password is hashed, not stored in plain text."""
        mock_repo = AsyncMock()
        mock_repo.find_by_email.return_value = None
        
        created_entity = UserEntity(
            id=EntityId.generate(),
            email=Email("user@example.com"),
            display_name="Test User",
            password_hash="$2b$12$hashed_password",
            role=UserRole.VIEWER
        )
        mock_repo.save.return_value = created_entity
        
        use_case = RegisterUserUseCase(mock_repo, jwt_handler)
        
        payload = UserCreateRequest(
            display_name="Test User",
            email="user@example.com",
            password="PlainPassword123"
        )
        
        await use_case.execute(payload)
        
        # Check that save was called with hashed password
        save_call_args = mock_repo.save.call_args[0][0]
        assert save_call_args.password_hash != "PlainPassword123"
        assert save_call_args.password_hash.startswith("$2b$")

    @pytest.mark.asyncio
    async def test_execute_converts_email_to_lowercase(self, jwt_handler):
        """Test that email is normalized to lowercase."""
        mock_repo = AsyncMock()
        mock_repo.find_by_email.return_value = None
        
        created_entity = UserEntity(
            id=EntityId.generate(),
            email=Email("user@example.com"),
            display_name="Test User",
            password_hash="hashed",
            role=UserRole.VIEWER
        )
        mock_repo.save.return_value = created_entity
        
        use_case = RegisterUserUseCase(mock_repo, jwt_handler)
        
        payload = UserCreateRequest(
            display_name="Test User",
            email="User@Example.COM",  # Mixed case
            password="SecurePass123"
        )
        
        result = await use_case.execute(payload)
        
        assert result.email == "user@example.com"
