from unittest.mock import AsyncMock, patch

from src.app.features.auth.application.dtos.auth_dto import ResendVerificationResponse, VerifyEmailResponse
from src.app.features.auth.domain.exceptions.auth_exceptions import (
    EmailNotVerifiedError,
    InvalidVerificationCodeError,
    VerificationRateLimitedError,
)


VERIFY_EXECUTE = "src.app.features.auth.application.use_cases.verify_email.VerifyEmailUseCase.execute"
RESEND_EXECUTE = "src.app.features.auth.application.use_cases.resend_verification.ResendVerificationUseCase.execute"
LOGIN_EXECUTE = "src.app.features.auth.application.use_cases.login_user.LoginUserUseCase.execute"


class TestVerifyEmailEndpoint:
    def test_valid_code_returns_verified(self, client):
        with patch(VERIFY_EXECUTE, new=AsyncMock(return_value=VerifyEmailResponse(verified=True))):
            response = client.post("/v1/auth/verify-email", json={"email": "new@example.com", "code": "ABC234"})

        assert response.status_code == 200
        assert response.json() == {"verified": True}

    def test_invalid_code_returns_400(self, client):
        with patch(VERIFY_EXECUTE, new=AsyncMock(side_effect=InvalidVerificationCodeError())):
            response = client.post("/v1/auth/verify-email", json={"email": "new@example.com", "code": "ZZZ999"})

        assert response.status_code == 400
        assert response.json()["detail"] == "Invalid or expired verification code"

    def test_locked_code_returns_429(self, client):
        with patch(
            VERIFY_EXECUTE,
            new=AsyncMock(side_effect=VerificationRateLimitedError("Too many attempts. Please request a new code.")),
        ):
            response = client.post("/v1/auth/verify-email", json={"email": "new@example.com", "code": "ABC234"})

        assert response.status_code == 429
        assert "request a new code" in response.json()["detail"]

    def test_missing_code_returns_422(self, client):
        response = client.post("/v1/auth/verify-email", json={"email": "new@example.com"})

        assert response.status_code == 422


class TestResendVerificationEndpoint:
    def test_resend_returns_generic_message(self, client):
        with patch(
            RESEND_EXECUTE,
            new=AsyncMock(return_value=ResendVerificationResponse(message="If this email is awaiting verification")),
        ):
            response = client.post("/v1/auth/resend-verification", json={"email": "new@example.com"})

        assert response.status_code == 200
        assert "awaiting verification" in response.json()["message"]

    def test_resend_limit_returns_429(self, client):
        with patch(
            RESEND_EXECUTE,
            new=AsyncMock(side_effect=VerificationRateLimitedError("Too many code requests.")),
        ):
            response = client.post("/v1/auth/resend-verification", json={"email": "new@example.com"})

        assert response.status_code == 429


class TestLoginBeforeVerification:
    def test_unverified_login_returns_403_with_a_stable_code(self, client):
        with patch(LOGIN_EXECUTE, new=AsyncMock(side_effect=EmailNotVerifiedError())):
            response = client.post("/v1/auth/login", json={"email": "new@example.com", "password": "SecurePass1"})

        assert response.status_code == 403
        assert response.json() == {
            "detail": "Please verify your email before signing in.",
            "code": "EMAIL_NOT_VERIFIED",
        }


class TestVerifyEmailRequestBounds:
    def test_oversized_code_is_rejected_before_reaching_the_use_case(self, client):
        execute = AsyncMock()
        with patch(VERIFY_EXECUTE, new=execute):
            response = client.post("/v1/auth/verify-email", json={"email": "new@example.com", "code": "A" * 100})

        assert response.status_code == 422
        execute.assert_not_called()
