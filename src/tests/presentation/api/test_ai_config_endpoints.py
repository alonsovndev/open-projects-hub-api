"""API tests for the AI credits and API key endpoints (api-contract §17/§18)."""

import logging
from datetime import UTC, datetime
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from src.app.config.app_config import AppConfig
from src.app.features.ai_config.application.dtos.ai_config_dto import (
    ApiKeyResponse,
    CreditBalanceResponse,
    ListApiKeysResponse,
    ValidateApiKeyResponse,
)
from src.app.features.ai_config.domain.exceptions.ai_config_exceptions import (
    ApiKeyNotFoundError,
    ApiKeyRejectedError,
    KeyValidationRateLimitedError,
)
from src.app.features.ai_config.domain.value_objects.ai_provider import AIProvider
from src.app.features.ai_config.domain.value_objects.provider_failure_reason import ProviderFailureReason
from src.app.features.user.domain.exceptions.user_exceptions import AICreditsExhaustedError
from src.app.shared.infrastructure.security.jwt_handler import JWTHandler


RAW_KEY = "sk-proj-abcdefghijklmnopqrstuv1234"

SAVE_USE_CASE = "src.app.features.ai_config.application.use_cases.save_api_key.SaveApiKeyUseCase.execute"
LIST_USE_CASE = "src.app.features.ai_config.application.use_cases.list_api_keys.ListApiKeysUseCase.execute"
DELETE_USE_CASE = "src.app.features.ai_config.application.use_cases.delete_api_key.DeleteApiKeyUseCase.execute"
VALIDATE_USE_CASE = "src.app.features.ai_config.application.use_cases.validate_api_key.ValidateApiKeyUseCase.execute"
CREDITS_USE_CASE = "src.app.features.ai_config.application.use_cases.get_credit_balance.GetCreditBalanceUseCase.execute"


@pytest.fixture
def app_jwt_handler():
    """JWT handler using the app's configured secret key."""
    config = AppConfig.instance()
    return JWTHandler(secret_key=config.get_config("jwt.secret_key"), expiration_minutes=60, validate_secret=False)


@pytest.fixture
def admin_token(app_jwt_handler):
    """Generate admin JWT token for tests."""
    return app_jwt_handler.create_access_token(
        user_id="550e8400-e29b-41d4-a716-446655440001",
        email="admin@example.com",
        role="admin",
        workspace_id="550e8400-e29b-41d4-a716-4466554400ff",
    )


def auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def serialize_records(records) -> str:
    """
    Render log records the way the production JSON formatter does — extras included.

    `caplog.text` shows only the formatted message, so asserting against it would pass
    even while a secret sat in `record.extra`.
    """
    return "\n".join(repr(record.__dict__) for record in records)


class TestCreditBalanceEndpoint:
    """GET /v1/users/me/credits."""

    def test_returns_the_contracted_shape(self, client: TestClient, admin_token: str):
        with patch(
            CREDITS_USE_CASE,
            new=AsyncMock(return_value=CreditBalanceResponse(credits=3, total_granted=5)),
        ):
            response = client.get("/v1/users/me/credits", headers=auth(admin_token))

        assert response.status_code == 200
        assert response.json() == {"credits": 3, "totalGranted": 5}

    def test_requires_authentication(self, client: TestClient):
        assert client.get("/v1/users/me/credits").status_code == 401


class TestListApiKeysEndpoint:
    """GET /v1/users/me/api-keys."""

    def test_returns_masked_keys_in_camel_case(self, client: TestClient, admin_token: str):
        configured_at = datetime(2026, 8, 11, 10, 0, tzinfo=UTC)
        with patch(
            LIST_USE_CASE,
            new=AsyncMock(
                return_value=ListApiKeysResponse(
                    keys=[
                        ApiKeyResponse(
                            provider=AIProvider.OPENAI,
                            masked_key="sk-proj***...1234",
                            configured_at=configured_at,
                        )
                    ]
                )
            ),
        ):
            response = client.get("/v1/users/me/api-keys", headers=auth(admin_token))

        assert response.status_code == 200
        key = response.json()["keys"][0]
        assert key["provider"] == "openai"
        assert key["maskedKey"] == "sk-proj***...1234"
        assert "configuredAt" in key

    def test_response_never_carries_a_plaintext_key(self, client: TestClient, admin_token: str):
        """NFR-010-02: there is no field through which the raw key could escape."""
        with patch(
            LIST_USE_CASE,
            new=AsyncMock(
                return_value=ListApiKeysResponse(
                    keys=[
                        ApiKeyResponse(
                            provider=AIProvider.OPENAI,
                            masked_key="sk-proj***...1234",
                            configured_at=datetime.now(tz=UTC),
                        )
                    ]
                )
            ),
        ):
            response = client.get("/v1/users/me/api-keys", headers=auth(admin_token))

        assert RAW_KEY not in response.text
        assert "apiKey" not in response.text


class TestSaveApiKeyEndpoint:
    """POST /v1/users/me/api-keys."""

    def test_returns_201_with_the_mask(self, client: TestClient, admin_token: str):
        with patch(
            SAVE_USE_CASE,
            new=AsyncMock(
                return_value=ApiKeyResponse(
                    provider=AIProvider.OPENAI,
                    masked_key="sk-proj***...1234",
                    configured_at=datetime.now(tz=UTC),
                )
            ),
        ):
            response = client.post(
                "/v1/users/me/api-keys",
                json={"provider": "openai", "apiKey": RAW_KEY},
                headers=auth(admin_token),
            )

        assert response.status_code == 201
        assert response.json()["maskedKey"] == "sk-proj***...1234"
        assert RAW_KEY not in response.text

    def test_a_refused_key_returns_422_with_guidance(self, client: TestClient, admin_token: str):
        with patch(
            SAVE_USE_CASE,
            new=AsyncMock(side_effect=ApiKeyRejectedError(AIProvider.OPENAI, ProviderFailureReason.AUTH_FAILED)),
        ):
            response = client.post(
                "/v1/users/me/api-keys",
                json={"provider": "openai", "apiKey": RAW_KEY},
                headers=auth(admin_token),
            )

        assert response.status_code == 422
        body = response.json()
        assert body["code"] == "API_KEY_INVALID"
        assert body["promptsKeyUpdate"] is True
        assert body["detail"] == "API key rejected by OpenAI. Check your key in Settings."
        assert RAW_KEY not in response.text

    def test_a_spent_validation_budget_returns_429_with_retry_after(self, client: TestClient, admin_token: str):
        with patch(
            SAVE_USE_CASE,
            new=AsyncMock(side_effect=KeyValidationRateLimitedError(retry_after_seconds=1800)),
        ):
            response = client.post(
                "/v1/users/me/api-keys",
                json={"provider": "openai", "apiKey": RAW_KEY},
                headers=auth(admin_token),
            )

        assert response.status_code == 429
        assert response.headers["Retry-After"] == "1800"

    def test_rejects_an_unsupported_provider(self, client: TestClient, admin_token: str):
        response = client.post(
            "/v1/users/me/api-keys",
            json={"provider": "anthropic", "apiKey": RAW_KEY},
            headers=auth(admin_token),
        )
        assert response.status_code == 422

    def test_rejects_an_empty_key(self, client: TestClient, admin_token: str):
        response = client.post(
            "/v1/users/me/api-keys",
            json={"provider": "openai", "apiKey": ""},
            headers=auth(admin_token),
        )
        assert response.status_code == 422


class TestDeleteApiKeyEndpoint:
    """DELETE /v1/users/me/api-keys/{provider}."""

    def test_returns_204(self, client: TestClient, admin_token: str):
        with patch(DELETE_USE_CASE, new=AsyncMock(return_value=None)):
            response = client.delete("/v1/users/me/api-keys/openai", headers=auth(admin_token))

        assert response.status_code == 204

    def test_returns_404_when_no_key_is_configured(self, client: TestClient, admin_token: str):
        with patch(DELETE_USE_CASE, new=AsyncMock(side_effect=ApiKeyNotFoundError(AIProvider.GEMINI))):
            response = client.delete("/v1/users/me/api-keys/gemini", headers=auth(admin_token))

        assert response.status_code == 404

    def test_rejects_an_unsupported_provider(self, client: TestClient, admin_token: str):
        response = client.delete("/v1/users/me/api-keys/anthropic", headers=auth(admin_token))
        assert response.status_code == 422


class TestValidateApiKeyEndpoint:
    """POST /v1/users/me/api-keys/{provider}/validate."""

    def test_reports_a_working_key(self, client: TestClient, admin_token: str):
        with patch(
            VALIDATE_USE_CASE,
            new=AsyncMock(return_value=ValidateApiKeyResponse(provider=AIProvider.OPENAI, valid=True)),
        ):
            response = client.post("/v1/users/me/api-keys/openai/validate", headers=auth(admin_token))

        assert response.status_code == 200
        assert response.json() == {"provider": "openai", "valid": True, "quotaWarning": False}

    def test_surfaces_a_low_quota_warning(self, client: TestClient, admin_token: str):
        with patch(
            VALIDATE_USE_CASE,
            new=AsyncMock(
                return_value=ValidateApiKeyResponse(provider=AIProvider.OPENAI, valid=True, quota_warning=True)
            ),
        ):
            response = client.post("/v1/users/me/api-keys/openai/validate", headers=auth(admin_token))

        assert response.json()["quotaWarning"] is True

    def test_a_quota_failure_does_not_prompt_a_key_update(self, client: TestClient, admin_token: str):
        """An exhausted quota is not a bad key, so FR-010-11's modal must not fire."""
        with patch(
            VALIDATE_USE_CASE,
            new=AsyncMock(side_effect=ApiKeyRejectedError(AIProvider.OPENAI, ProviderFailureReason.QUOTA_EXHAUSTED)),
        ):
            response = client.post("/v1/users/me/api-keys/openai/validate", headers=auth(admin_token))

        assert response.status_code == 422
        assert response.json()["promptsKeyUpdate"] is False


class TestRefinementCreditExhaustion:
    """POST /v1/refinement/generate-stories surfaces credit exhaustion as 402."""

    def test_exhausted_credits_return_402(self, client: TestClient, admin_token: str):
        with patch(
            "src.app.features.refinement.application.use_cases."
            "generate_stories_from_notes.GenerateStoriesFromNotesUseCase.execute",
            new=AsyncMock(side_effect=AICreditsExhaustedError),
        ):
            response = client.post(
                "/v1/refinement/generate-stories",
                json={
                    "projectId": "550e8400-e29b-41d4-a716-446655440001",
                    "rawNotes": "Some discovery notes long enough to pass validation",
                },
                headers=auth(admin_token),
            )

        assert response.status_code == 402
        body = response.json()
        assert body["code"] == "INSUFFICIENT_CREDITS"
        assert "Add your own API key" in body["detail"]

    def test_accepts_an_explicit_provider_selection(self, client: TestClient, admin_token: str):
        """FR-010-06: the caller picks the provider for the run."""
        captured = {}

        async def capture(self, request, ctx):
            captured["provider"] = request.provider
            raise AICreditsExhaustedError

        with patch(
            "src.app.features.refinement.application.use_cases."
            "generate_stories_from_notes.GenerateStoriesFromNotesUseCase.execute",
            new=capture,
        ):
            client.post(
                "/v1/refinement/generate-stories",
                json={
                    "projectId": "550e8400-e29b-41d4-a716-446655440001",
                    "rawNotes": "Some discovery notes long enough to pass validation",
                    "provider": "openai",
                },
                headers=auth(admin_token),
            )

        assert captured["provider"] == "openai"


class TestValidationErrorsDoNotLeakKeys:
    """
    NFR-010-02 at the framework boundary.

    A key that fails Pydantic validation never reaches the use case, so the use-case-level
    redaction tests cannot see it. FastAPI's RequestValidationError carries the rejected
    value in `errors()[i]["input"]`, and the JSON log formatter copies every `extra`
    through verbatim — so this is the one path where a raw key could reach CloudWatch.
    """

    def test_an_over_long_key_is_not_written_to_the_logs(self, client: TestClient, admin_token: str, caplog):
        over_long_key = "sk-proj-" + "LEAKCANARY" * 60

        with caplog.at_level(logging.DEBUG):
            response = client.post(
                "/v1/users/me/api-keys",
                json={"provider": "openai", "apiKey": over_long_key},
                headers=auth(admin_token),
            )

        assert response.status_code == 422
        assert "LEAKCANARY" not in response.text
        # `caplog.text` only renders the message, so the `extra` payload has to be
        # inspected directly — that is exactly where the rejected value would sit, and
        # what the production JSON formatter serializes.
        assert "LEAKCANARY" not in serialize_records(caplog.records)

    def test_a_malformed_body_still_reports_which_field_failed(self, client: TestClient, admin_token: str, caplog):
        """Redaction must not cost the diagnostics the log is there to provide."""
        with caplog.at_level(logging.WARNING):
            response = client.post(
                "/v1/users/me/api-keys",
                json={"provider": "openai"},
                headers=auth(admin_token),
            )

        assert response.status_code == 422
        assert "apiKey" in serialize_records(caplog.records)
