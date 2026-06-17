"""Tests for logging utilities: redact_sensitive_fields and mask_email."""

from src.app.shared.logging.utils import mask_email, redact_sensitive_fields


class TestRedactSensitiveFields:
    """Tests for redact_sensitive_fields function."""

    def test_redacts_password_field(self):
        data = {"username": "john", "password": "secret123", "email": "john@example.com"}
        result = redact_sensitive_fields(data)

        assert result["username"] == "john"
        assert result["email"] == "john@example.com"
        assert result["password"] == "***REDACTED***"

    def test_redacts_token_field(self):
        data = {"user_id": "123", "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"}
        result = redact_sensitive_fields(data)

        assert result["user_id"] == "123"
        assert result["access_token"] == "***REDACTED***"

    def test_redacts_multiple_sensitive_fields(self):
        data = {
            "username": "john",
            "password": "secret123",
            "api_key": "sk_live_abc123",
            "token": "bearer_xyz",
            "name": "John Doe",
        }
        result = redact_sensitive_fields(data)

        assert result["username"] == "john"
        assert result["name"] == "John Doe"
        assert result["password"] == "***REDACTED***"
        assert result["api_key"] == "***REDACTED***"
        assert result["token"] == "***REDACTED***"

    def test_handles_case_insensitive_keys(self):
        data = {"Password": "secret", "TOKEN": "xyz", "ApiKey": "abc"}
        result = redact_sensitive_fields(data)

        assert result["Password"] == "***REDACTED***"
        assert result["TOKEN"] == "***REDACTED***"
        assert result["ApiKey"] == "***REDACTED***"

    def test_returns_new_dict_without_modifying_original(self):
        original = {"username": "john", "password": "secret"}
        result = redact_sensitive_fields(original)

        assert original["password"] == "secret"
        assert result["password"] == "***REDACTED***"
        assert original is not result

    def test_handles_empty_dict(self):
        result = redact_sensitive_fields({})
        assert result == {}

    def test_handles_dict_without_sensitive_fields(self):
        data = {"username": "john", "email": "john@example.com", "age": 30}
        result = redact_sensitive_fields(data)

        assert result == data


class TestMaskEmail:
    """Tests for mask_email function."""

    def test_masks_standard_email(self):
        result = mask_email("john.doe@example.com")
        assert result == "jo***@example.com"

    def test_masks_short_email(self):
        result = mask_email("a@example.com")
        assert result == "a***@example.com"

    def test_masks_long_email(self):
        result = mask_email("verylongemailaddress@example.com")
        assert result == "ve***@example.com"

    def test_shows_custom_number_of_chars(self):
        result = mask_email("john.doe@example.com", show_chars=3)
        assert result == "joh***@example.com"

    def test_handles_invalid_email(self):
        result = mask_email("not-an-email")
        assert result == "***INVALID_EMAIL***"

    def test_handles_email_without_at_sign(self):
        result = mask_email("johnexample.com")
        assert result == "***INVALID_EMAIL***"
