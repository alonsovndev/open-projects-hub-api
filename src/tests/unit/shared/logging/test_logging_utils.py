"""Tests for logging utilities and sensitive data handling."""

from unittest.mock import MagicMock

from src.app.shared.logging.utils import log_business_event, log_error_event, mask_email, redact_sensitive_fields


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


class TestLogBusinessEvent:
    """Tests for log_business_event function."""

    def test_logs_basic_event(self):
        mock_logger = MagicMock()

        log_business_event(
            logger=mock_logger,
            event_type="project.created",
            message="Project created successfully",
        )

        mock_logger.info.assert_called_once()
        call_args = mock_logger.info.call_args

        assert call_args[0][0] == "Project created successfully"
        assert call_args[1]["extra"]["event_type"] == "project.created"

    def test_logs_event_with_entity_id(self):
        mock_logger = MagicMock()

        log_business_event(
            logger=mock_logger,
            event_type="project.updated",
            message="Project updated",
            entity_id="proj-123",
        )

        call_args = mock_logger.info.call_args
        assert call_args[1]["extra"]["entity_id"] == "proj-123"

    def test_logs_event_with_user_id(self):
        mock_logger = MagicMock()

        log_business_event(
            logger=mock_logger,
            event_type="project.deleted",
            message="Project deleted",
            user_id="user-456",
        )

        call_args = mock_logger.info.call_args
        assert call_args[1]["extra"]["user_id"] == "user-456"

    def test_logs_event_with_additional_data(self):
        mock_logger = MagicMock()

        log_business_event(
            logger=mock_logger,
            event_type="project.created",
            message="Project created",
            additional_data={"project_name": "Test Project", "priority": "high"},
        )

        call_args = mock_logger.info.call_args
        assert call_args[1]["extra"]["project_name"] == "Test Project"
        assert call_args[1]["extra"]["priority"] == "high"

    def test_redacts_sensitive_data_in_additional_data(self):
        mock_logger = MagicMock()

        log_business_event(
            logger=mock_logger,
            event_type="user.updated",
            message="User updated",
            additional_data={
                "username": "john",
                "password": "secret123",  # Should be redacted
                "email": "john@example.com",
            },
        )

        call_args = mock_logger.info.call_args
        assert call_args[1]["extra"]["username"] == "john"
        assert call_args[1]["extra"]["email"] == "john@example.com"
        assert call_args[1]["extra"]["password"] == "***REDACTED***"

    def test_uses_different_log_levels(self):
        mock_logger = MagicMock()

        log_business_event(
            logger=mock_logger,
            event_type="test.event",
            message="Test message",
            level="warning",
        )

        mock_logger.warning.assert_called_once()
        mock_logger.info.assert_not_called()


class TestLogErrorEvent:
    """Tests for log_error_event function."""

    def test_logs_error_without_exception(self):
        mock_logger = MagicMock()

        log_error_event(
            logger=mock_logger,
            error_type="validation.failed",
            message="Validation error occurred",
        )

        mock_logger.error.assert_called_once()
        call_args = mock_logger.error.call_args

        assert call_args[0][0] == "Validation error occurred"
        assert call_args[1]["extra"]["error_type"] == "validation.failed"

    def test_logs_error_with_exception(self):
        mock_logger = MagicMock()
        test_error = ValueError("Invalid input")

        log_error_event(
            logger=mock_logger,
            error_type="validation.failed",
            message="Validation error",
            error=test_error,
        )

        mock_logger.exception.assert_called_once()
        call_args = mock_logger.exception.call_args

        assert call_args[1]["extra"]["error_class"] == "ValueError"
        assert call_args[1]["extra"]["error_message"] == "Invalid input"

    def test_logs_error_with_entity_context(self):
        mock_logger = MagicMock()

        log_error_event(
            logger=mock_logger,
            error_type="database.error",
            message="Failed to save entity",
            entity_id="proj-123",
            user_id="user-456",
        )

        call_args = mock_logger.error.call_args
        assert call_args[1]["extra"]["entity_id"] == "proj-123"
        assert call_args[1]["extra"]["user_id"] == "user-456"

    def test_redacts_sensitive_data_in_error_context(self):
        mock_logger = MagicMock()

        log_error_event(
            logger=mock_logger,
            error_type="auth.failed",
            message="Authentication failed",
            additional_data={
                "username": "john",
                "password": "secret123",  # Should be redacted
            },
        )

        call_args = mock_logger.error.call_args
        assert call_args[1]["extra"]["username"] == "john"
        assert call_args[1]["extra"]["password"] == "***REDACTED***"
