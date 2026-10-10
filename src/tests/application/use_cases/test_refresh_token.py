"""
Tests for RefreshTokenUseCase.
"""

from unittest.mock import AsyncMock

import jwt as pyjwt
import pytest
import pytest_asyncio

from src.app.features.auth.application.use_cases.refresh_token import RefreshTokenRequest, RefreshTokenUseCase
from src.app.features.user.domain.entities.user_entity import UserEntity, UserRole
from src.app.shared.domain.value_objects.email import Email
from src.app.shared.domain.value_objects.entity_id import EntityId
from src.app.shared.infrastructure.security.jwt_handler import JWTHandler
from src.app.shared.infrastructure.security.token_revocation_service import get_token_revocation_service


@pytest_asyncio.fixture(autouse=True)
async def clear_token_revocation():
    """Clear token revocation service before each test."""
    service = get_token_revocation_service()
    await service.clear_all()
    yield
    await service.clear_all()


@pytest.fixture
def jwt_handler():
    """Create JWT handler for tests."""
    return JWTHandler(
        secret_key="test-secret-key-that-is-at-least-32-characters-long",
        algorithm="HS256",
        expiration_minutes=15,
        refresh_expiration_minutes=1440,
        validate_secret=False,
    )


@pytest.fixture
def user_entity():
    """Create test user entity."""
    return UserEntity(
        id=EntityId.from_string("550e8400-e29b-41d4-a716-446655440000"),
        email=Email("test@example.com"),
        password_hash="hashed_password",
        display_name="Test User",
        role=UserRole.MEMBER,
    )


@pytest.fixture
def mock_user_repository():
    """Create mock user repository."""
    return AsyncMock()


class TestRefreshTokenUseCase:
    """Test suite for RefreshTokenUseCase."""

    @pytest.mark.asyncio
    async def test_refresh_token_returns_new_tokens(self, jwt_handler, user_entity, mock_user_repository):
        """Test that refresh token returns new access and refresh tokens."""
        # Create refresh token
        refresh_token = jwt_handler.create_refresh_token(
            user_id=str(user_entity.id),
            email=str(user_entity.email),
            role=user_entity.role.value,
        )

        # Mock repository to return user
        mock_user_repository.find_by_email = AsyncMock(return_value=user_entity)

        # Create use case
        use_case = RefreshTokenUseCase(mock_user_repository, jwt_handler)

        # Execute
        request = RefreshTokenRequest(refresh_token=refresh_token)
        response = await use_case.execute(request)

        # Verify new tokens are returned
        assert response.access_token is not None
        assert response.refresh_token is not None
        assert response.refresh_token != refresh_token

        # Verify new access token is valid
        access_payload = jwt_handler.decode_access_token(response.access_token)
        assert access_payload["sub"] == str(user_entity.id)
        assert access_payload["email"] == str(user_entity.email)
        assert access_payload["role"] == user_entity.role.value

        # Verify new refresh token is valid
        refresh_payload = jwt_handler.decode_refresh_token(response.refresh_token)
        assert refresh_payload["sub"] == str(user_entity.id)
        assert refresh_payload["type"] == "refresh"

    @pytest.mark.asyncio
    async def test_refresh_token_raises_error_for_expired_token(self, user_entity, mock_user_repository):
        """Test that expired refresh token raises ExpiredSignatureError."""
        # Create JWT handler with very short expiration
        short_jwt_handler = JWTHandler(
            secret_key="test-secret-key-that-is-at-least-32-characters-long",
            algorithm="HS256",
            expiration_minutes=15,
            refresh_expiration_minutes=-1,  # Expired immediately
            validate_secret=False,
        )

        # Create expired refresh token
        expired_token = short_jwt_handler.create_refresh_token(
            user_id=str(user_entity.id),
            email=str(user_entity.email),
            role=user_entity.role.value,
        )

        # Create use case
        use_case = RefreshTokenUseCase(mock_user_repository, short_jwt_handler)

        # Execute should raise ExpiredSignatureError
        request = RefreshTokenRequest(refresh_token=expired_token)
        with pytest.raises(pyjwt.ExpiredSignatureError):
            await use_case.execute(request)

    @pytest.mark.asyncio
    async def test_refresh_token_raises_error_for_invalid_token(self, jwt_handler, mock_user_repository):
        """Test that invalid refresh token raises InvalidTokenError."""
        use_case = RefreshTokenUseCase(mock_user_repository, jwt_handler)

        request = RefreshTokenRequest(refresh_token="invalid.token.here")
        with pytest.raises(pyjwt.InvalidTokenError):
            await use_case.execute(request)

    @pytest.mark.asyncio
    async def test_refresh_token_raises_error_when_user_not_found(self, jwt_handler, user_entity, mock_user_repository):
        """Test that refresh token raises error when user not found."""
        # Create valid refresh token
        refresh_token = jwt_handler.create_refresh_token(
            user_id=str(user_entity.id),
            email=str(user_entity.email),
            role=user_entity.role.value,
        )

        # Mock repository to return None (user not found)
        mock_user_repository.find_by_email = AsyncMock(return_value=None)

        # Create use case
        use_case = RefreshTokenUseCase(mock_user_repository, jwt_handler)

        # Execute should raise ValueError
        request = RefreshTokenRequest(refresh_token=refresh_token)
        with pytest.raises(ValueError, match="User not found"):
            await use_case.execute(request)

    @pytest.mark.asyncio
    async def test_refresh_token_raises_error_for_access_token(self, jwt_handler, user_entity, mock_user_repository):
        """Test that using access token instead of refresh token raises error."""
        # Create access token (not refresh token)
        access_token = jwt_handler.create_access_token(
            user_id=str(user_entity.id),
            email=str(user_entity.email),
            role=user_entity.role.value,
        )

        # Create use case
        use_case = RefreshTokenUseCase(mock_user_repository, jwt_handler)

        # Execute should raise InvalidTokenError (not a refresh token)
        request = RefreshTokenRequest(refresh_token=access_token)
        with pytest.raises(pyjwt.InvalidTokenError, match="not a refresh token"):
            await use_case.execute(request)

    @pytest.mark.asyncio
    async def test_refresh_token_cannot_be_reused(self, jwt_handler, user_entity, mock_user_repository):
        """Test that refresh token cannot be reused after one use (single-use token)."""
        # Create refresh token
        refresh_token = jwt_handler.create_refresh_token(
            user_id=str(user_entity.id),
            email=str(user_entity.email),
            role=user_entity.role.value,
        )

        # Mock repository to return user
        mock_user_repository.find_by_email = AsyncMock(return_value=user_entity)

        # Create use case
        use_case = RefreshTokenUseCase(mock_user_repository, jwt_handler)

        # First use should succeed
        request = RefreshTokenRequest(refresh_token=refresh_token)
        response1 = await use_case.execute(request)
        assert response1.access_token is not None
        assert response1.refresh_token is not None

        # Second use of same token should fail (token revoked)
        with pytest.raises(pyjwt.InvalidTokenError, match="already been used"):
            await use_case.execute(request)

    @pytest.mark.asyncio
    async def test_concurrent_reuse_loses_the_revocation_race(self, jwt_handler, user_entity, mock_user_repository):
        """A request that passes the reuse check but finds the token already revoked must not mint tokens."""
        refresh_token = jwt_handler.create_refresh_token(
            user_id=str(user_entity.id),
            email=str(user_entity.email),
            role=user_entity.role.value,
        )
        mock_user_repository.find_by_email = AsyncMock(return_value=user_entity)
        token_revocation = AsyncMock()
        token_revocation.is_revoked = AsyncMock(return_value=False)
        token_revocation.revoke_token = AsyncMock(return_value=False)
        use_case = RefreshTokenUseCase(mock_user_repository, jwt_handler, token_revocation)

        with pytest.raises(pyjwt.InvalidTokenError, match="already been used"):
            await use_case.execute(RefreshTokenRequest(refresh_token=refresh_token))


class TestRefreshTokenSessionLifetime:
    """Test remember-me propagation and forced-logout rejection (US-EP2-BE-004)."""

    @pytest.mark.asyncio
    async def test_remember_me_session_carries_forward_on_rotation(
        self, jwt_handler, user_entity, mock_user_repository
    ):
        """A remember-me refresh token should mint a remember-me token on rotation too."""
        refresh_token = jwt_handler.create_refresh_token(
            user_id=str(user_entity.id),
            email=str(user_entity.email),
            role=user_entity.role.value,
            remember_me=True,
        )
        mock_user_repository.find_by_email = AsyncMock(return_value=user_entity)

        use_case = RefreshTokenUseCase(mock_user_repository, jwt_handler)
        response = await use_case.execute(RefreshTokenRequest(refresh_token=refresh_token))

        new_payload = jwt_handler.decode_refresh_token(response.refresh_token)
        assert new_payload["remember_me"] is True
        assert response.session_expires_at is not None

    @pytest.mark.asyncio
    async def test_forced_logout_rejects_stale_token_version(self, jwt_handler, mock_user_repository):
        """A refresh token issued before a forced logout (token_version bump) is rejected."""
        current_user = UserEntity(
            id=EntityId.from_string("550e8400-e29b-41d4-a716-446655440000"),
            email=Email("test@example.com"),
            password_hash="hashed_password",
            display_name="Test User",
            role=UserRole.MEMBER,
            token_version=1,  # bumped since the token below was issued at version 0
        )
        stale_refresh_token = jwt_handler.create_refresh_token(
            user_id=str(current_user.id),
            email=str(current_user.email),
            role=current_user.role.value,
            token_version=0,
        )
        mock_user_repository.find_by_email = AsyncMock(return_value=current_user)

        use_case = RefreshTokenUseCase(mock_user_repository, jwt_handler)

        with pytest.raises(pyjwt.InvalidTokenError, match="revoked"):
            await use_case.execute(RefreshTokenRequest(refresh_token=stale_refresh_token))
