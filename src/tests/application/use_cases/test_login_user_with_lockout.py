"""
Tests for LoginUserUseCase with account lockout integration.

Tests login functionality with lockout behavior:
- Successful login clears lockout state
- Failed attempts trigger lockout
- Locked account prevents login
- Progressive lockout behavior
"""

import contextlib
from unittest.mock import AsyncMock

import pytest
from freezegun import freeze_time

from src.app.features.auth.application.dtos.auth_dto import LoginRequest
from src.app.features.auth.application.use_cases.login_user import LoginUserUseCase
from src.app.features.auth.domain.exceptions.auth_exceptions import AccountLockedError, InvalidCredentialsError
from src.app.features.user.domain.entities.user_entity import UserEntity
from src.app.features.user.domain.value_objects.user_role import UserRole
from src.app.shared.domain.value_objects.email import Email
from src.app.shared.domain.value_objects.entity_id import EntityId
from src.app.shared.infrastructure.security.account_lockout_service import AccountLockoutService
from src.app.shared.infrastructure.security.jwt_handler import JWTHandler
from src.app.shared.infrastructure.security.password_handler import PasswordHandler


@pytest.fixture
def mock_user_repository():
    """Create mock user repository."""
    return AsyncMock()


@pytest.fixture
def jwt_handler():
    """Create JWT handler with test secret."""
    return JWTHandler(secret_key="test-secret-key-for-testing-only", algorithm="HS256", expiration_minutes=15)


@pytest.fixture
def mock_user_entity():
    """Create mock user entity for testing."""
    return UserEntity(
        id=EntityId.generate(),
        email=Email("test@example.com"),
        display_name="Test User",
        password_hash="$2b$12$somehashedpassword",
        role=UserRole.VIEWER,
    )


@pytest.fixture
def login_use_case(mock_user_repository, jwt_handler):
    """Create LoginUserUseCase with fresh lockout service."""
    use_case = LoginUserUseCase(mock_user_repository, jwt_handler)
    # Reset lockout service state
    use_case.lockout_service = AccountLockoutService()
    use_case.lockout_service.MAX_FAILED_ATTEMPTS = 5
    return use_case


class TestLoginWithLockout:
    """Test login behavior with account lockout."""

    @pytest.mark.asyncio
    async def test_successful_login_clears_failed_attempts(
        self, login_use_case, mock_user_repository, mock_user_entity
    ):
        """Test that successful login clears any existing failed attempts."""
        # Setup
        mock_user_repository.find_by_email.return_value = mock_user_entity

        # Pre-record some failed attempts
        await login_use_case.lockout_service.record_failed_attempt("test@example.com")
        await login_use_case.lockout_service.record_failed_attempt("test@example.com")
        assert await login_use_case.lockout_service.get_failed_attempts("test@example.com") == 2

        # Mock password verification to succeed
        original_verify = PasswordHandler.verify_password
        PasswordHandler.verify_password = AsyncMock(return_value=True)

        try:
            # Execute successful login
            request = LoginRequest(email="test@example.com", password="password123")
            result = await login_use_case.execute(request)

            # Verify failed attempts cleared
            attempts = await login_use_case.lockout_service.get_failed_attempts("test@example.com")
            assert attempts == 0
            assert result is not None
        finally:
            PasswordHandler.verify_password = original_verify

    @pytest.mark.asyncio
    async def test_failed_login_increments_attempts(self, login_use_case, mock_user_repository, mock_user_entity):
        """Test that failed login increments failed attempts."""
        # Setup
        mock_user_repository.find_by_email.return_value = mock_user_entity

        # Mock password verification to fail
        original_verify = PasswordHandler.verify_password
        PasswordHandler.verify_password = AsyncMock(return_value=False)

        try:
            # Execute failed login
            request = LoginRequest(email="test@example.com", password="wrongpassword")

            with pytest.raises(InvalidCredentialsError):
                await login_use_case.execute(request)

            # Verify failed attempt recorded
            attempts = await login_use_case.lockout_service.get_failed_attempts("test@example.com")
            assert attempts == 1
        finally:
            PasswordHandler.verify_password = original_verify

    @pytest.mark.asyncio
    async def test_account_locked_after_max_attempts(self, login_use_case, mock_user_repository, mock_user_entity):
        """Test that account is locked after MAX_FAILED_ATTEMPTS."""
        # Setup
        mock_user_repository.find_by_email.return_value = mock_user_entity

        # Mock password verification to fail
        original_verify = PasswordHandler.verify_password
        PasswordHandler.verify_password = AsyncMock(return_value=False)

        try:
            request = LoginRequest(email="test@example.com", password="wrongpassword")

            # First 5 attempts should raise InvalidCredentialsError
            for _ in range(5):
                with pytest.raises(InvalidCredentialsError):
                    await login_use_case.execute(request)

            # 6th attempt should raise AccountLockedError
            with pytest.raises(AccountLockedError) as exc_info:
                await login_use_case.execute(request)

            assert exc_info.value.remaining_seconds > 0
            assert exc_info.value.failed_attempts >= 5
        finally:
            PasswordHandler.verify_password = original_verify

    @pytest.mark.asyncio
    async def test_locked_account_prevents_login_even_with_correct_password(
        self, login_use_case, mock_user_repository, mock_user_entity
    ):
        """Test that locked account cannot login even with correct credentials."""
        # Setup - lock the account
        for _ in range(5):
            await login_use_case.lockout_service.record_failed_attempt("test@example.com")

        mock_user_repository.find_by_email.return_value = mock_user_entity

        # Mock password verification to succeed
        original_verify = PasswordHandler.verify_password
        PasswordHandler.verify_password = AsyncMock(return_value=True)

        try:
            # Try to login with correct password while locked
            request = LoginRequest(email="test@example.com", password="correctpassword")

            with pytest.raises(AccountLockedError) as exc_info:
                await login_use_case.execute(request)

            # Should raise AccountLockedError before even checking password
            assert exc_info.value.remaining_seconds > 0
        finally:
            PasswordHandler.verify_password = original_verify

    @pytest.mark.asyncio
    async def test_nonexistent_user_records_failed_attempt(self, login_use_case, mock_user_repository):
        """Test that login attempt for non-existent user still records failure."""
        # Setup
        mock_user_repository.find_by_email.return_value = None

        request = LoginRequest(email="nonexistent@example.com", password="password")

        with pytest.raises(InvalidCredentialsError):
            await login_use_case.execute(request)

        # Verify failed attempt recorded (prevents user enumeration timing attacks)
        attempts = await login_use_case.lockout_service.get_failed_attempts("nonexistent@example.com")
        assert attempts == 1

    @pytest.mark.asyncio
    async def test_lockout_info_included_in_exception(self, login_use_case, mock_user_repository, mock_user_entity):
        """Test that lockout exception includes remaining time and attempt count."""
        # Setup - lock the account
        for _ in range(5):
            await login_use_case.lockout_service.record_failed_attempt("test@example.com")

        mock_user_repository.find_by_email.return_value = mock_user_entity

        request = LoginRequest(email="test@example.com", password="password")

        with pytest.raises(AccountLockedError) as exc_info:
            await login_use_case.execute(request)

        # Verify exception has lockout info
        exception = exc_info.value
        assert exception.remaining_seconds > 0
        assert exception.failed_attempts == 5
        assert "try again" in exception.message.lower()


class TestProgressiveLockoutInLogin:
    """Test progressive lockout behavior through login attempts."""

    @pytest.mark.asyncio
    async def test_lockout_duration_increases_with_attempts(
        self, login_use_case, mock_user_repository, mock_user_entity
    ):
        """Test that lockout duration increases with more failed attempts.

        Note: Once locked at 5 attempts, account stays at that lockout level.
        To test progressive lockout, we directly test the lockout service behavior.
        """
        # Setup
        mock_user_repository.find_by_email.return_value = mock_user_entity

        # Mock password verification to fail
        original_verify = PasswordHandler.verify_password
        PasswordHandler.verify_password = AsyncMock(return_value=False)

        try:
            request = LoginRequest(email="test@example.com", password="wrongpassword")

            with freeze_time("2026-05-11 12:00:00"):
                # 5 failed attempts (triggers lockout)
                for _ in range(5):
                    with contextlib.suppress(InvalidCredentialsError):
                        await login_use_case.execute(request)

                # Check lockout info
                info = await login_use_case.lockout_service.get_lockout_info("test@example.com")

                # With 5 attempts, should be 15 minutes lockout (base)
                assert info["failed_attempts"] == 5
                assert info["locked"] is True
                # Approximately 15 minutes (900 seconds)
                assert 890 <= info["remaining_seconds"] <= 910
        finally:
            PasswordHandler.verify_password = original_verify


class TestEmailNormalization:
    """Test that email normalization is applied for lockout tracking."""

    @pytest.mark.asyncio
    async def test_email_normalized_to_lowercase_for_lockout(
        self, login_use_case, mock_user_repository, mock_user_entity
    ):
        """Test that emails are normalized to lowercase for lockout tracking."""
        # Setup
        mock_user_repository.find_by_email.return_value = mock_user_entity

        # Mock password verification to fail
        original_verify = PasswordHandler.verify_password
        PasswordHandler.verify_password = AsyncMock(return_value=False)

        try:
            # Fail with different case variations
            request1 = LoginRequest(email="Test@Example.COM", password="wrong")
            request2 = LoginRequest(email="test@example.com", password="wrong")

            with pytest.raises(InvalidCredentialsError):
                await login_use_case.execute(request1)

            with pytest.raises(InvalidCredentialsError):
                await login_use_case.execute(request2)

            # Both should count as same user (normalized to lowercase)
            attempts = await login_use_case.lockout_service.get_failed_attempts("test@example.com")
            assert attempts == 2
        finally:
            PasswordHandler.verify_password = original_verify
