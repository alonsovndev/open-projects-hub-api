from unittest.mock import AsyncMock, patch

from src.app.features.auth.application.dtos.auth_dto import ForgotPasswordResponse, ResetPasswordResponse
from src.app.features.auth.domain.exceptions.auth_exceptions import InvalidResetCodeError, ResetCodeRateLimitedError


class TestForgotPasswordEndpoint:
    def test_forgot_password_returns_generic_message(self, client):
        with patch(
            "src.app.features.auth.application.use_cases.request_password_reset.RequestPasswordResetUseCase.execute",
            new=AsyncMock(
                return_value=ForgotPasswordResponse(
                    message="If an account exists for this email, a reset code has been sent."
                )
            ),
        ):
            response = client.post("/v1/auth/forgot-password", json={"email": "admin@example.com"})

        assert response.status_code == 200
        assert "reset code" in response.json()["message"]

    def test_forgot_password_rejects_malformed_email(self, client):
        response = client.post("/v1/auth/forgot-password", json={"email": "not-an-email"})

        assert response.status_code == 422


class TestResendResetCodeEndpoint:
    def test_resend_within_limit_returns_generic_message(self, client):
        with patch(
            "src.app.features.auth.application.use_cases.resend_reset_code.ResendResetCodeUseCase.execute",
            new=AsyncMock(
                return_value=ForgotPasswordResponse(
                    message="If an account exists for this email, a reset code has been sent."
                )
            ),
        ):
            response = client.post("/v1/auth/resend-reset-code", json={"email": "admin@example.com"})

        assert response.status_code == 200

    def test_resend_over_limit_returns_429(self, client):
        with patch(
            "src.app.features.auth.application.use_cases.resend_reset_code.ResendResetCodeUseCase.execute",
            new=AsyncMock(side_effect=ResetCodeRateLimitedError("Too many reset code requests.")),
        ):
            response = client.post("/v1/auth/resend-reset-code", json={"email": "admin@example.com"})

        assert response.status_code == 429


class TestResetPasswordEndpoint:
    def test_reset_password_success(self, client):
        with patch(
            "src.app.features.auth.application.use_cases.confirm_password_reset.ConfirmPasswordResetUseCase.execute",
            new=AsyncMock(return_value=ResetPasswordResponse(message="Password has been reset successfully.")),
        ):
            response = client.post(
                "/v1/auth/reset-password",
                json={"email": "admin@example.com", "code": "ABC234", "newPassword": "NewPassw0rd"},
            )

        assert response.status_code == 200

    def test_reset_password_invalid_code_returns_404(self, client):
        with patch(
            "src.app.features.auth.application.use_cases.confirm_password_reset.ConfirmPasswordResetUseCase.execute",
            new=AsyncMock(side_effect=InvalidResetCodeError()),
        ):
            response = client.post(
                "/v1/auth/reset-password",
                json={"email": "admin@example.com", "code": "WRONG1", "newPassword": "NewPassw0rd"},
            )

        assert response.status_code == 404

    def test_reset_password_rate_limited_returns_429(self, client):
        with patch(
            "src.app.features.auth.application.use_cases.confirm_password_reset.ConfirmPasswordResetUseCase.execute",
            new=AsyncMock(side_effect=ResetCodeRateLimitedError("Too many attempts.")),
        ):
            response = client.post(
                "/v1/auth/reset-password",
                json={"email": "admin@example.com", "code": "ABC234", "newPassword": "NewPassw0rd"},
            )

        assert response.status_code == 429

    def test_reset_password_weak_password_returns_400(self, client):
        with patch(
            "src.app.features.auth.application.use_cases.confirm_password_reset.ConfirmPasswordResetUseCase.execute",
            new=AsyncMock(side_effect=ValueError("Password must be at least 8 characters long")),
        ):
            response = client.post(
                "/v1/auth/reset-password",
                json={"email": "admin@example.com", "code": "ABC234", "newPassword": "short"},
            )

        assert response.status_code == 400
