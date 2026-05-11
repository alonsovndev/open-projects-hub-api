import pytest
import pytest_asyncio
from unittest.mock import AsyncMock

from src.app.features.user.application.dtos.auth_dto import LoginRequest
from src.app.features.user.application.use_cases.login_user import LoginUserUseCase
from src.app.features.user.domain.entities.user_entity import UserEntity
from src.app.features.user.domain.exceptions.auth_exceptions import InvalidCredentialsError
from src.app.features.user.domain.value_objects.email import Email
from src.app.features.user.domain.value_objects.user_role import UserRole
from src.app.shared.domain.value_objects.entity_id import EntityId
from src.app.shared.infrastructure.security.jwt_handler import JWTHandler
from src.app.shared.infrastructure.security.password_handler import PasswordHandler


@pytest.fixture
def jwt_handler():
    return JWTHandler(
        secret_key="test-secret-key-that-is-at-least-32-characters-long",
        expiration_minutes=60,
        validate_secret=False  # Disable validation for tests
    )


@pytest_asyncio.fixture
async def mock_admin_user():
    password_hash = await PasswordHandler.hash_password("Admin123!")
    return UserEntity(
        id=EntityId.generate(),
        email=Email("admin@example.com"),
        display_name="Admin User",
        password_hash=password_hash,
        role=UserRole.ADMIN,
    )


class TestLoginUserUseCase:

    @pytest.mark.asyncio
    async def test_execute_returns_response_with_token(self, jwt_handler, mock_admin_user):
        """Test that successful login returns AdminLoginResponse with a token."""
        mock_repo = AsyncMock()
        mock_repo.find_by_email.return_value = mock_admin_user

        use_case = LoginUserUseCase(mock_repo, jwt_handler)
        payload = LoginRequest(email="admin@example.com", password="Admin123!")

        result = await use_case.execute(payload)

        assert result.token is not None
        assert result.access_token == result.token
        assert result.email == "admin@example.com"
        assert result.display_name == "Admin User"
        assert result.role == "admin"
        assert result.user.email == "admin@example.com"

    @pytest.mark.asyncio
    async def test_execute_raises_invalid_credentials_when_user_not_found(self, jwt_handler):
        """Test that missing user raises InvalidCredentialsError."""
        mock_repo = AsyncMock()
        mock_repo.find_by_email.return_value = None

        use_case = LoginUserUseCase(mock_repo, jwt_handler)
        payload = LoginRequest(email="ghost@example.com", password="password")

        with pytest.raises(InvalidCredentialsError):
            await use_case.execute(payload)

    @pytest.mark.asyncio
    async def test_execute_raises_invalid_credentials_for_wrong_password(
        self, jwt_handler, mock_admin_user
    ):
        """Test that wrong password raises InvalidCredentialsError."""
        mock_repo = AsyncMock()
        mock_repo.find_by_email.return_value = mock_admin_user

        use_case = LoginUserUseCase(mock_repo, jwt_handler)
        payload = LoginRequest(email="admin@example.com", password="WrongPassword")

        with pytest.raises(InvalidCredentialsError):
            await use_case.execute(payload)

    @pytest.mark.asyncio
    async def test_execute_sets_correct_role_in_response(self, jwt_handler):
        """Test that role is correctly set in response."""
        password_hash = await PasswordHandler.hash_password("User123!")
        regular_user = UserEntity(
            id=EntityId.generate(),
            email=Email("user@example.com"),
            display_name="Regular User",
            password_hash=password_hash,
            role=UserRole.VIEWER,
        )

        mock_repo = AsyncMock()
        mock_repo.find_by_email.return_value = regular_user

        use_case = LoginUserUseCase(mock_repo, jwt_handler)
        payload = LoginRequest(email="user@example.com", password="User123!")

        result = await use_case.execute(payload)

        assert result.role == "viewer"
