from datetime import UTC, datetime
from unittest.mock import AsyncMock, patch

import pytest
import pytest_asyncio

from src.app.app import fastapi_app
from src.app.composition import get_login_use_case, get_logout_use_case, get_refresh_token_use_case
from src.app.composition.infrastructure import get_jwt_handler
from src.app.config.app_config import AppConfig
from src.app.features.auth.application.dtos.auth_dto import AdminLoginResponse, UserDetail
from src.app.features.auth.application.use_cases.logout_user import LogoutUseCase
from src.app.features.auth.application.use_cases.refresh_token import RefreshTokenUseCase
from src.app.features.auth.presentation.browser_session import REFRESH_COOKIE
from src.app.features.user.domain.entities.user_entity import UserEntity
from src.app.features.user.domain.value_objects.user_role import UserRole
from src.app.features.workspaces.domain.entities.workspace_entity import WorkspaceEntity
from src.app.shared.domain.value_objects.email import Email
from src.app.shared.domain.value_objects.entity_id import EntityId
from src.app.shared.infrastructure.rate_limit.rate_limiter import limiter
from src.app.shared.infrastructure.security.jwt_handler import JWTHandler
from src.app.shared.infrastructure.security.token_revocation_service import get_token_revocation_service


BROWSER_HEADERS = {"Origin": "http://localhost:5173", "X-Session-Mode": "cookie"}
LOGIN_BODY = {"email": "browser@example.com", "password": "fixture-password"}


@pytest_asyncio.fixture(autouse=True)
async def isolate_revocations():
    limiter.reset()
    await get_token_revocation_service().clear_all()
    yield
    limiter.reset()
    await get_token_revocation_service().clear_all()


@pytest.fixture
def session_services():
    jwt_handler = JWTHandler(secret_key="browser-session-fixture-key-at-least-32-characters", validate_secret=False)
    workspace = WorkspaceEntity.create("Current workspace")
    user = UserEntity(
        id=EntityId.generate(),
        email=Email("browser@example.com"),
        display_name="Current user",
        password_hash="unused",
        role=UserRole.MEMBER,
        workspace_id=workspace.id,
    )
    user_repository = AsyncMock()
    user_repository.find_by_email.return_value = user
    workspace_repository = AsyncMock()
    workspace_repository.find_by_id.return_value = workspace

    async def login(payload):
        refresh_token = jwt_handler.create_refresh_token(
            str(user.id), str(user.email), "admin", remember_me=payload.remember_me
        )
        return AdminLoginResponse(
            access_token=jwt_handler.create_access_token(str(user.id), str(user.email), "admin"),
            refresh_token=refresh_token,
            session_expires_at=jwt_handler.get_token_expiry(refresh_token).isoformat(),
            user=UserDetail(
                email=str(user.email), display_name="Old display name", name="Old display name", role="admin"
            ),
            token="legacy-token",
            email=str(user.email),
            display_name="Old display name",
            role="admin",
            logged_in_at=datetime.now(UTC).isoformat(),
        )

    login_use_case = AsyncMock()
    login_use_case.execute.side_effect = login
    refresh_use_case = RefreshTokenUseCase(user_repository, jwt_handler, workspace_repository=workspace_repository)
    logout_use_case = LogoutUseCase(jwt_handler)
    fastapi_app.dependency_overrides[get_jwt_handler] = lambda: jwt_handler
    fastapi_app.dependency_overrides[get_login_use_case] = lambda: login_use_case
    fastapi_app.dependency_overrides[get_refresh_token_use_case] = lambda: refresh_use_case
    fastapi_app.dependency_overrides[get_logout_use_case] = lambda: logout_use_case
    yield jwt_handler, login_use_case
    for dependency in (get_jwt_handler, get_login_use_case, get_refresh_token_use_case, get_logout_use_case):
        fastapi_app.dependency_overrides.pop(dependency, None)


@pytest.mark.parametrize("remember", [False, True])
def test_browser_login_cookie_attributes_and_lifetime(client, session_services, remember):
    response = client.post("/v1/auth/login", headers=BROWSER_HEADERS, json={**LOGIN_BODY, "rememberMe": remember})
    assert response.status_code == 200
    assert set(response.json()) == {"accessToken", "sessionExpiresAt", "user"}
    cookie = response.headers["set-cookie"]
    assert "HttpOnly" in cookie and "SameSite=lax" in cookie and "Path=/v1/auth" in cookie
    assert "Domain=" not in cookie and "Secure" not in cookie
    assert ("Max-Age=" in cookie) is remember
    assert response.headers["cache-control"] == "no-store"
    claims = session_services[0].decode_refresh_token(client.cookies[REFRESH_COOKIE])
    assert claims["remember_me"] is remember
    assert (
        6 * 86400 < claims["exp"] - claims["iat"] <= 7 * 86400 if remember else claims["exp"] - claims["iat"] == 86400
    )


def test_secure_cookie_outside_local_and_test(client, session_services):
    with patch.object(AppConfig.instance(), "env", "prod"):
        response = client.post("/v1/auth/login", headers=BROWSER_HEADERS, json=LOGIN_BODY)
    assert response.status_code == 200
    assert "Secure" in response.headers["set-cookie"]


@pytest.mark.parametrize("endpoint", ["login", "refresh", "logout"])
@pytest.mark.parametrize("origin", [None, "null", "https://attacker.example", "http://localhost:5173.attacker.example"])
def test_cookie_operations_reject_untrusted_origin_before_execution(client, session_services, endpoint, origin):
    headers = {"X-Session-Mode": "cookie"}
    if origin is not None:
        headers["Origin"] = origin
    response = client.post(f"/v1/auth/{endpoint}", headers=headers, json=LOGIN_BODY if endpoint == "login" else None)
    assert response.status_code == 403
    assert "set-cookie" not in response.headers
    session_services[1].execute.assert_not_called()


def test_cookies_cannot_select_mode_without_custom_header(client, session_services):
    client.post("/v1/auth/login", headers=BROWSER_HEADERS, json=LOGIN_BODY)
    assert client.post("/v1/auth/refresh", headers={"Origin": BROWSER_HEADERS["Origin"]}).status_code == 422
    assert client.post("/v1/auth/logout", headers={"Origin": BROWSER_HEADERS["Origin"]}).status_code == 401


@pytest.mark.parametrize("endpoint", ["refresh", "logout"])
def test_cookie_mode_rejects_body_credentials(client, session_services, endpoint):
    client.post("/v1/auth/login", headers=BROWSER_HEADERS, json=LOGIN_BODY)
    response = client.post(f"/v1/auth/{endpoint}", headers=BROWSER_HEADERS, json={"refreshToken": "body-token"})
    assert response.status_code == 422


def test_rotation_is_unique_and_restores_current_metadata_then_logout_blocks_replay(client, session_services):
    client.post("/v1/auth/login", headers=BROWSER_HEADERS, json=LOGIN_BODY)
    first_cookie = client.cookies[REFRESH_COOKIE]
    first = client.post("/v1/auth/refresh", headers=BROWSER_HEADERS)
    assert first.status_code == 200
    second_cookie = client.cookies[REFRESH_COOKIE]
    assert second_cookie != first_cookie
    assert first.json()["user"] == {
        "email": "browser@example.com",
        "displayName": "Current user",
        "name": "Current user",
        "role": "member",
        "workspace": {"id": first.json()["user"]["workspace"]["id"], "name": "Current workspace"},
    }
    assert "refreshToken" not in first.json()
    second = client.post("/v1/auth/refresh", headers=BROWSER_HEADERS)
    assert second.status_code == 200
    third_cookie = client.cookies[REFRESH_COOKIE]
    assert third_cookie not in (first_cookie, second_cookie)
    logged_out = client.post("/v1/auth/logout", headers=BROWSER_HEADERS)
    assert logged_out.status_code == 200 and client.cookies.get(REFRESH_COOKIE) is None
    assert "Max-Age=0" in logged_out.headers["set-cookie"]
    for token in (first_cookie, second_cookie, third_cookie):
        assert client.post("/v1/auth/refresh", json={"refreshToken": token}).status_code == 401


def test_invalid_cookie_is_deleted_and_auth_failures_are_not_cached(client, session_services):
    client.cookies.set(REFRESH_COOKIE, "invalid", path="/v1/auth")
    response = client.post("/v1/auth/refresh", headers=BROWSER_HEADERS)
    assert response.status_code == 401
    assert "Max-Age=0" in response.headers["set-cookie"]
    assert response.headers["cache-control"] == "no-store"


def test_legacy_json_mode_keeps_refresh_tokens_and_does_not_set_cookies(client, session_services):
    login = client.post("/v1/auth/login", json=LOGIN_BODY)
    assert login.status_code == 200
    assert "refreshToken" in login.json() and "token" in login.json()
    assert "set-cookie" not in login.headers
    refresh = client.post("/v1/auth/refresh", json={"refreshToken": login.json()["refreshToken"]})
    assert refresh.status_code == 200 and "refreshToken" in refresh.json()
    assert "set-cookie" not in refresh.headers


def test_same_second_refresh_tokens_have_unique_identifiers(session_services):
    handler = session_services[0]
    now = datetime.now(UTC)
    with patch("src.app.shared.infrastructure.security.jwt_handler.datetime") as clock:
        clock.now.return_value = now
        first = handler.create_refresh_token("user", "browser@example.com", "member")
        second = handler.create_refresh_token("user", "browser@example.com", "member")
    assert first != second
    assert handler.decode_refresh_token(first)["jti"] != handler.decode_refresh_token(second)["jti"]


@pytest.mark.parametrize("origin", ["http://localhost:5174", "http://127.0.0.1:5173"])
def test_loopback_fallback_origins_are_local_only(client, session_services, origin):
    with patch.object(AppConfig.instance(), "env", "local"):
        assert client.post("/v1/auth/logout", headers={**BROWSER_HEADERS, "Origin": origin}).status_code == 200
    with patch.object(AppConfig.instance(), "env", "prod"):
        assert client.post("/v1/auth/logout", headers={**BROWSER_HEADERS, "Origin": origin}).status_code == 403
