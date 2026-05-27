from datetime import datetime, timedelta, timezone

import jwt
import pytest

from src.app.shared.infrastructure.security.jwt_handler import JWTHandler


class TestJWTHandler:
    @pytest.fixture
    def jwt_handler(self):
        return JWTHandler(
            secret_key="test-secret-key-that-is-at-least-32-characters-long",
            algorithm="HS256",
            expiration_minutes=60,
            validate_secret=False,  # Disable validation for tests
        )

    def test_create_access_token_includes_claims(self, jwt_handler):
        """Test that token contains expected claims."""
        token = jwt_handler.create_access_token(
            user_id="123",
            email="test@example.com",
            role="ADMIN",
        )

        payload = jwt.decode(
            token,
            jwt_handler.secret_key,
            algorithms=["HS256"],
            options={"verify_signature": True, "verify_aud": False, "verify_iss": False},
        )

        assert payload["sub"] == "123"
        assert payload["email"] == "test@example.com"
        assert payload["role"] == "ADMIN"
        assert "iat" in payload
        assert "exp" in payload
        assert payload["aud"] == "open-projects-hub-api"
        assert payload["iss"] == "open-projects-hub-api"

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
            "aud": "open-projects-hub-api",
            "iss": "open-projects-hub-api",
        }

        expired_token = jwt.encode(payload, jwt_handler.secret_key, algorithm="HS256")

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
        past_time = datetime.now(tz=UTC) - timedelta(hours=2)
        exp_time = past_time + timedelta(hours=1)

        payload = {
            "sub": "123",
            "email": "test@example.com",
            "role": "USER",
            "iat": past_time,
            "exp": exp_time,
            "aud": "open-projects-hub-api",
            "iss": "open-projects-hub-api",
        }

        expired_token = jwt.encode(payload, jwt_handler.secret_key, algorithm="HS256")

        assert jwt_handler.verify_token(expired_token) is False

    def test_create_access_token_with_additional_claims(self, jwt_handler):
        """Test that additional claims are included in the token."""
        token = jwt_handler.create_access_token(
            user_id="123",
            email="test@example.com",
            role="ADMIN",
            additional_claims={"custom_claim": "value"},
        )

        payload = jwt.decode(
            token,
            jwt_handler.secret_key,
            algorithms=["HS256"],
            options={"verify_signature": True, "verify_aud": False, "verify_iss": False},
        )

        assert payload["custom_claim"] == "value"

    def test_decode_token_with_invalid_audience_raises_error(self, jwt_handler):
        """Test that token with wrong audience is rejected."""
        token = jwt_handler.create_access_token(
            user_id="123",
            email="test@example.com",
            role="USER",
        )

        # Create a handler with different audience
        other_handler = JWTHandler(
            secret_key="test-secret-key-that-is-at-least-32-characters-long",
            algorithm="HS256",
            expiration_minutes=60,
            validate_secret=False,
            audience="different-audience",
        )

        with pytest.raises(jwt.InvalidAudienceError):
            other_handler.decode_access_token(token)

    def test_decode_token_with_invalid_issuer_raises_error(self, jwt_handler):
        """Test that token with wrong issuer is rejected."""
        token = jwt_handler.create_access_token(
            user_id="123",
            email="test@example.com",
            role="USER",
        )

        # Create a handler with different issuer
        other_handler = JWTHandler(
            secret_key="test-secret-key-that-is-at-least-32-characters-long",
            algorithm="HS256",
            expiration_minutes=60,
            validate_secret=False,
            issuer="different-issuer",
        )

        with pytest.raises(jwt.InvalidIssuerError):
            other_handler.decode_access_token(token)

    def test_decode_token_missing_required_claims_raises_error(self, jwt_handler):
        """Test that token missing required claims is rejected."""
        # Create a token missing the 'aud' claim
        payload = {
            "sub": "123",
            "email": "test@example.com",
            "role": "USER",
            "iat": datetime.now(tz=UTC),
            "exp": datetime.now(tz=UTC) + timedelta(hours=1),
            "iss": "open-projects-hub-api",
            # Missing "aud" claim
        }

        token = jwt.encode(payload, jwt_handler.secret_key, algorithm="HS256")

        with pytest.raises(jwt.InvalidTokenError):
            jwt_handler.decode_access_token(token)

    def test_custom_audience_and_issuer(self):
        """Test that custom audience and issuer can be set and validated."""
        handler = JWTHandler(
            secret_key="test-secret-key-that-is-at-least-32-characters-long",
            algorithm="HS256",
            expiration_minutes=60,
            validate_secret=False,
            audience="custom-audience",
            issuer="custom-issuer",
        )

        token = handler.create_access_token(
            user_id="123",
            email="test@example.com",
            role="USER",
        )

        payload = handler.decode_access_token(token)

        assert payload["aud"] == "custom-audience"
        assert payload["iss"] == "custom-issuer"
