import pytest
import pytest_asyncio

from src.app.config.app_config import AppConfig
from src.app.shared.infrastructure.security.jwt_handler import JWTHandler
from src.app.shared.infrastructure.security.token_revocation_service import get_token_revocation_service


@pytest_asyncio.fixture(autouse=True)
async def clear_token_revocation():
    """Test config keeps revocation state in-memory; isolate it between tests."""
    service = get_token_revocation_service()
    await service.clear_all()
    yield
    await service.clear_all()


@pytest.fixture
def app_jwt_handler():
    """JWT handler using the app's configured secret key (test profile keeps auth state in-memory)."""
    config = AppConfig.instance()
    secret_key = config.get_config("jwt.secret_key")
    return JWTHandler(secret_key=secret_key, expiration_minutes=60, validate_secret=False)


@pytest.fixture
def admin_access_token(app_jwt_handler):
    return app_jwt_handler.create_access_token(
        user_id="550e8400-e29b-41d4-a716-446655440123", email="admin@example.com", role="admin"
    )


@pytest.fixture
def admin_refresh_token(app_jwt_handler):
    return app_jwt_handler.create_refresh_token(
        user_id="550e8400-e29b-41d4-a716-446655440123", email="admin@example.com", role="admin"
    )


class TestLogoutEndpoint:
    def test_logout_without_auth_header_returns_401(self, client, admin_refresh_token):
        response = client.post("/v1/auth/logout", json={"refreshToken": admin_refresh_token})

        assert response.status_code == 401

    def test_logout_revokes_refresh_token_and_rejects_replay(self, client, admin_access_token, admin_refresh_token):
        logout_response = client.post(
            "/v1/auth/logout",
            headers={"Authorization": f"Bearer {admin_access_token}"},
            json={"refreshToken": admin_refresh_token},
        )
        assert logout_response.status_code == 200
        assert logout_response.json()["message"]

        refresh_response = client.post("/v1/auth/refresh", json={"refreshToken": admin_refresh_token})
        assert refresh_response.status_code == 401

    def test_logout_is_idempotent_for_already_invalid_token(self, client, admin_access_token):
        response = client.post(
            "/v1/auth/logout",
            headers={"Authorization": f"Bearer {admin_access_token}"},
            json={"refreshToken": "not-a-real-token"},
        )

        assert response.status_code == 200
