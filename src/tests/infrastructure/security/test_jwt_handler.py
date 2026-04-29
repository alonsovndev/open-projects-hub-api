import pytest
from datetime import datetime, timedelta, timezone

import jwt

from src.shared.infrastructure.security.jwt_handler import JWTHandler


class TestJWTHandler:

    @pytest.fixture
    def jwt_handler(self):
        return JWTHandler(
            secret_key="test-secret-key",
            algorithm="HS256",
            expiration_minutes=60,
        )

    def test_create_access_token_includes_claims(self, jwt_handler):
        """Test that token contains expected claims."""
        token = jwt_handler.create_access_token(
            user_id="123",
            email="test@example.com",
            role="ADMIN",
        )

        payload = jwt.decode(token, "test-secret-key", algorithms=["HS256"])

        assert payload["sub"] == "123"
        assert payload["email"] == "test@example.com"
        assert payload["role"] == "ADMIN"
        assert "iat" in payload
        assert "exp" in payload

    def test_decode_access_token_returns_payload(self, jwt_handler):
        """Test decoding a valid token."""
        token = jwt_handler.create_access_token(
            user_id="123",
            email="test@example.com",
            role="USER",
        )

        payload = jwt_handler.decode_access_token(token)

        assert payload["sub"] == "123"
        assert payload["email"] == "test@example.com"

    def test_decode_expired_token_raises_error(self, jwt_handler):
        """Test that expired token raises error."""
        past_time = datetime.now(tz=timezone.utc) - timedelta(hours=2)
        exp_time = past_time + timedelta(hours=1)

        payload = {
            "sub": "123",
            "email": "test@example.com",
            "role": "USER",
            "iat": past_time,
            "exp": exp_time,
        }

        expired_token = jwt.encode(payload, "test-secret-key", algorithm="HS256")

        with pytest.raises(jwt.ExpiredSignatureError):
            jwt_handler.decode_access_token(expired_token)

    def test_decode_invalid_token_raises_error(self, jwt_handler):
        """Test that invalid token raises error."""
        invalid_token = "invalid.token.here"

        with pytest.raises(jwt.InvalidTokenError):
            jwt_handler.decode_access_token(invalid_token)

    def test_verify_token_returns_true_for_valid(self, jwt_handler):
        """Test token verification for valid token."""
        token = jwt_handler.create_access_token(
            user_id="123",
            email="test@example.com",
            role="USER",
        )

        assert jwt_handler.verify_token(token) is True

    def test_verify_token_returns_false_for_invalid(self, jwt_handler):
        """Test token verification for invalid token."""
        assert jwt_handler.verify_token("invalid.token") is False

    def test_verify_token_returns_false_for_expired(self, jwt_handler):
        """Test that expired token fails verification."""
        past_time = datetime.now(tz=timezone.utc) - timedelta(hours=2)
        exp_time = past_time + timedelta(hours=1)

        payload = {
            "sub": "123",
            "email": "test@example.com",
            "role": "USER",
            "iat": past_time,
            "exp": exp_time,
        }

        expired_token = jwt.encode(payload, "test-secret-key", algorithm="HS256")

        assert jwt_handler.verify_token(expired_token) is False

    def test_create_access_token_with_additional_claims(self, jwt_handler):
        """Test that additional claims are included in the token."""
        token = jwt_handler.create_access_token(
            user_id="123",
            email="test@example.com",
            role="ADMIN",
            additional_claims={"custom_claim": "value"},
        )

        payload = jwt.decode(token, "test-secret-key", algorithms=["HS256"])

        assert payload["custom_claim"] == "value"
