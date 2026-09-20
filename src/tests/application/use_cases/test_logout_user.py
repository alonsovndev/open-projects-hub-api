"""
Tests for LogoutUseCase.
"""

import pytest

from src.app.features.auth.application.dtos.auth_dto import RefreshTokenRequest
from src.app.features.auth.application.use_cases.logout_user import LogoutUseCase
from src.app.shared.infrastructure.security.jwt_handler import JWTHandler
from src.app.shared.infrastructure.security.token_revocation_service import TokenRevocationService


@pytest.fixture
def jwt_handler():
    return JWTHandler(
        secret_key="test-secret-key-that-is-at-least-32-characters-long",
        algorithm="HS256",
        expiration_minutes=15,
        validate_secret=False,
    )


@pytest.fixture
def token_revocation():
    return TokenRevocationService()


@pytest.fixture
def use_case(jwt_handler, token_revocation):
    return LogoutUseCase(jwt_handler, token_revocation)


class TestLogoutUseCase:
    @pytest.mark.asyncio
    async def test_logout_revokes_refresh_token(self, use_case, jwt_handler, token_revocation):
        refresh_token = jwt_handler.create_refresh_token(user_id="user-1", email="a@example.com", role="admin")

        response = await use_case.execute(RefreshTokenRequest(refresh_token=refresh_token))

        assert response.message == "Logged out successfully."
        assert await token_revocation.is_revoked(refresh_token) is True

    @pytest.mark.asyncio
    async def test_logged_out_token_cannot_be_replayed(self, jwt_handler, token_revocation):
        from unittest.mock import AsyncMock

        from src.app.features.auth.application.use_cases.refresh_token import RefreshTokenUseCase

        refresh_token = jwt_handler.create_refresh_token(user_id="user-1", email="a@example.com", role="admin")
        logout_use_case = LogoutUseCase(jwt_handler, token_revocation)
        await logout_use_case.execute(RefreshTokenRequest(refresh_token=refresh_token))

        refresh_use_case = RefreshTokenUseCase(AsyncMock(), jwt_handler, token_revocation)
        import jwt as pyjwt

        with pytest.raises(pyjwt.InvalidTokenError, match="already been used"):
            await refresh_use_case.execute(RefreshTokenRequest(refresh_token=refresh_token))

    @pytest.mark.asyncio
    async def test_logout_is_idempotent_for_invalid_token(self, use_case):
        """An already-expired/garbage token should not raise — logout always succeeds."""
        response = await use_case.execute(RefreshTokenRequest(refresh_token="not-a-real-token"))

        assert response.message == "Logged out successfully."
