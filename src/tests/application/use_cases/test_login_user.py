from datetime import UTC, datetime
from unittest.mock import AsyncMock

import pytest
import pytest_asyncio

from src.app.features.auth.application.dtos.auth_dto import LoginRequest
from src.app.features.auth.application.use_cases.login_user import LoginUserUseCase
from src.app.features.auth.domain.exceptions.auth_exceptions import EmailNotVerifiedError, InvalidCredentialsError
from src.app.features.user.domain.entities.user_entity import UserEntity
from src.app.features.user.domain.value_objects.user_role import UserRole
from src.app.shared.domain.value_objects.email import Email
from src.app.shared.domain.value_objects.entity_id import EntityId
from src.app.shared.infrastructure.security.jwt_handler import JWTHandler
from src.app.shared.infrastructure.security.password_handler import PasswordHandler


@pytest.fixture
def jwt_handler():
    return JWTHandler(
        secret_key="test-secret-key-that-is-at-least-32-characters-long",
        expiration_minutes=60,
        validate_secret=False,  # Disable validation for tests
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
        email_verified_at=datetime.now(UTC),
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
    async def test_execute_raises_invalid_credentials_for_wrong_password(self, jwt_handler, mock_admin_user):
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
            role=UserRole.MEMBER,
            email_verified_at=datetime.now(UTC),
        )

        mock_repo = AsyncMock()
        mock_repo.find_by_email.return_value = regular_user

        use_case = LoginUserUseCase(mock_repo, jwt_handler)
        payload = LoginRequest(email="user@example.com", password="User123!")

        result = await use_case.execute(payload)

        assert result.role == "member"

    @pytest.mark.asyncio
    async def test_remember_me_issues_a_7_day_session(self, jwt_handler, mock_admin_user):
        """Standard login sessions are 24h; remember-me extends to 7 days (FR-007-06/07)."""
        mock_repo = AsyncMock()
        mock_repo.find_by_email.return_value = mock_admin_user
        use_case = LoginUserUseCase(mock_repo, jwt_handler)

        standard = await use_case.execute(LoginRequest(email="admin@example.com", password="Admin123!"))
        remembered = await use_case.execute(
            LoginRequest(email="admin@example.com", password="Admin123!", remember_me=True)
        )

        standard_payload = jwt_handler.decode_refresh_token(standard.refresh_token)
        remembered_payload = jwt_handler.decode_refresh_token(remembered.refresh_token)

        assert remembered_payload["exp"] - remembered_payload["iat"] > standard_payload["exp"] - standard_payload["iat"]
        assert remembered.session_expires_at is not None


class TestLoginRequiresVerifiedEmail:
    """FR-008-06: a self-registered account cannot sign in until its email is verified."""

    @staticmethod
    async def build_pending_user(password: str) -> UserEntity:
        return UserEntity.create_pending_verification(
            email="new@example.com",
            display_name="New User",
            password_hash=await PasswordHandler.hash_password(password),
        )

    @pytest.mark.asyncio
    async def test_correct_password_on_an_unverified_account_is_refused(self, jwt_handler):
        mock_repo = AsyncMock()
        mock_repo.find_by_email.return_value = await self.build_pending_user("Secure123!")

        use_case = LoginUserUseCase(mock_repo, jwt_handler)

        with pytest.raises(EmailNotVerifiedError):
            await use_case.execute(LoginRequest(email="new@example.com", password="Secure123!"))

    @pytest.mark.asyncio
    async def test_wrong_password_on_an_unverified_account_reveals_nothing(self, jwt_handler):
        """The verification state is only disclosed to someone who knows the password."""
        mock_repo = AsyncMock()
        mock_repo.find_by_email.return_value = await self.build_pending_user("Secure123!")

        use_case = LoginUserUseCase(mock_repo, jwt_handler)

        with pytest.raises(InvalidCredentialsError):
            await use_case.execute(LoginRequest(email="new@example.com", password="WrongPass1!"))

    @pytest.mark.asyncio
    async def test_login_succeeds_once_the_email_is_verified(self, jwt_handler):
        pending_user = await self.build_pending_user("Secure123!")
        pending_user.verify_email()
        mock_repo = AsyncMock()
        mock_repo.find_by_email.return_value = pending_user

        use_case = LoginUserUseCase(mock_repo, jwt_handler)
        result = await use_case.execute(LoginRequest(email="new@example.com", password="Secure123!"))

        assert result.token is not None
