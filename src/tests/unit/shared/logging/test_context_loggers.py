"""Tests for context-aware logger classes."""

import logging
from unittest.mock import MagicMock

from src.app.shared.logging.application_logger import ApplicationLogger
from src.app.shared.logging.business_logger import BusinessLogger
from src.app.shared.logging.context_logger import ContextLogger
from src.app.shared.logging.integration_logger import IntegrationLogger
from src.app.shared.logging.technical_logger import TechnicalLogger


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _mock_logger() -> MagicMock:
    """Create a mock logger for testing."""
    return MagicMock(spec=logging.Logger)


# ---------------------------------------------------------------------------
# ContextLogger
# ---------------------------------------------------------------------------


class TestContextLogger:
    """Tests for base ContextLogger class."""

    def test_info_logs_with_context(self):
        mock_log = _mock_logger()
        logger = ContextLogger(mock_log, context={"user_id": "user-123"})

        logger.info("Test message", extra_field="value")

        mock_log.info.assert_called_once_with("Test message", extra={"user_id": "user-123", "extra_field": "value"})

    def test_error_logs_without_exception(self):
        mock_log = _mock_logger()
        logger = ContextLogger(mock_log, context={"component": "test"})

        logger.error("Error occurred")

        mock_log.error.assert_called_once_with("Error occurred", extra={"component": "test"})

    def test_error_logs_with_exception(self):
        mock_log = _mock_logger()
        logger = ContextLogger(mock_log, context={"component": "test"})
        test_error = ValueError("invalid")

        logger.error("Error occurred", error=test_error)

        mock_log.exception.assert_called_once()
        call_args = mock_log.exception.call_args
        assert call_args[0][0] == "Error occurred"
        assert call_args[1]["extra"]["error_class"] == "ValueError"
        assert call_args[1]["extra"]["error_message"] == "invalid"
        assert call_args[1]["extra"]["component"] == "test"

    def test_warning_logs_with_context(self):
        mock_log = _mock_logger()
        logger = ContextLogger(mock_log, context={"user_id": "user-123"})

        logger.warning("Warning message")

        mock_log.warning.assert_called_once_with("Warning message", extra={"user_id": "user-123"})

    def test_debug_logs_with_context(self):
        mock_log = _mock_logger()
        logger = ContextLogger(mock_log, context={"component": "test"})

        logger.debug("Debug message")

        mock_log.debug.assert_called_once_with("Debug message", extra={"component": "test"})

    def test_empty_context(self):
        mock_log = _mock_logger()
        logger = ContextLogger(mock_log)

        logger.info("Test")

        mock_log.info.assert_called_once_with("Test", extra={})

    def test_with_context_merges(self):
        mock_log = _mock_logger()
        logger = ContextLogger(mock_log, context={"user_id": "user-123"})
        enriched = logger.with_context(request_id="req-456")

        enriched.info("Test")

        mock_log.info.assert_called_once_with("Test", extra={"user_id": "user-123", "request_id": "req-456"})

    def test_with_context_immutable(self):
        """Original logger context should not change after with_context."""
        mock_log = _mock_logger()
        logger = ContextLogger(mock_log, context={"user_id": "user-123"})
        logger.with_context(request_id="req-456")

        logger.info("Original")

        mock_log.info.assert_called_once_with("Original", extra={"user_id": "user-123"})

    def test_with_context_overrides(self):
        """Later context values should override earlier ones."""
        mock_log = _mock_logger()
        logger = ContextLogger(mock_log, context={"user_id": "old-id"})
        updated = logger.with_context(user_id="new-id")

        updated.info("Test")

        mock_log.info.assert_called_once_with("Test", extra={"user_id": "new-id"})


# ---------------------------------------------------------------------------
# BusinessLogger
# ---------------------------------------------------------------------------


class TestBusinessLogger:
    """Tests for BusinessLogger."""

    def test_init_sets_user_id(self):
        mock_log = _mock_logger()
        logger = BusinessLogger(mock_log, user_id="user-123")

        logger.info("test")

        mock_log.info.assert_called_once_with("test", extra={"user_id": "user-123", "logger_type": "business"})

    def test_event_logs_success(self):
        mock_log = _mock_logger()
        logger = BusinessLogger(mock_log, user_id="user-123")

        logger.event("project.created", entity_id="proj-456", project_name="Test Project")

        mock_log.info.assert_called_once()
        call_args = mock_log.info.call_args
        assert call_args[0][0] == "Project Created"
        assert call_args[1]["extra"]["event_type"] == "project.created"
        assert call_args[1]["extra"]["user_id"] == "user-123"
        assert call_args[1]["extra"]["entity_id"] == "proj-456"
        assert call_args[1]["extra"]["project_name"] == "Test Project"
        assert call_args[1]["extra"]["logger_type"] == "business"

    def test_event_with_custom_message(self):
        mock_log = _mock_logger()
        logger = BusinessLogger(mock_log, user_id="user-123")

        logger.event("project.created", message="Custom message")

        call_args = mock_log.info.call_args
        assert call_args[0][0] == "Custom message"

    def test_event_without_entity_id(self):
        mock_log = _mock_logger()
        logger = BusinessLogger(mock_log, user_id="user-123")

        logger.event("project.created")

        call_args = mock_log.info.call_args
        assert "entity_id" not in call_args[1]["extra"]

    def test_failure_logs_error(self):
        mock_log = _mock_logger()
        logger = BusinessLogger(mock_log, user_id="user-123")
        test_error = ValueError("Invalid client")

        logger.failure("project.create.client_not_found", error=test_error, client_id="client-456")

        mock_log.exception.assert_called_once()
        call_args = mock_log.exception.call_args
        assert call_args[0][0] == "Project Create Client Not Found"
        assert call_args[1]["extra"]["error_type"] == "project.create.client_not_found"
        assert call_args[1]["extra"]["client_id"] == "client-456"
        assert call_args[1]["extra"]["error_class"] == "ValueError"

    def test_failure_without_error(self):
        mock_log = _mock_logger()
        logger = BusinessLogger(mock_log, user_id="user-123")

        logger.failure("project.create.failed")

        mock_log.error.assert_called_once()

    def test_event_redacts_sensitive_data(self):
        mock_log = _mock_logger()
        logger = BusinessLogger(mock_log, user_id="user-123")

        logger.event("user.updated", password="secret123", email="user@example.com")

        call_args = mock_log.info.call_args
        assert call_args[1]["extra"]["password"] == "***REDACTED***"
        assert call_args[1]["extra"]["email"] == "user@example.com"

    def test_generate_message(self):
        msg = BusinessLogger._generate_message("project.created.success")
        assert msg == "Project Created Success"


# ---------------------------------------------------------------------------
# TechnicalLogger
# ---------------------------------------------------------------------------


class TestTechnicalLogger:
    """Tests for TechnicalLogger."""

    def test_init_sets_component(self):
        mock_log = _mock_logger()
        logger = TechnicalLogger(mock_log, component="database")

        logger.info("test")

        mock_log.info.assert_called_once_with("test", extra={"component": "database", "logger_type": "technical"})

    def test_operation_success(self):
        mock_log = _mock_logger()
        logger = TechnicalLogger(mock_log, component="database")

        logger.operation("db.insert", success=True, duration_ms=45.2, table="projects", rows_affected=1)

        mock_log.info.assert_called_once()
        call_args = mock_log.info.call_args
        assert call_args[0][0] == "db.insert succeeded"
        assert call_args[1]["extra"]["operation"] == "db.insert"
        assert call_args[1]["extra"]["success"] is True
        assert call_args[1]["extra"]["duration_ms"] == 45.2
        assert call_args[1]["extra"]["table"] == "projects"
        assert call_args[1]["extra"]["component"] == "database"

    def test_operation_failure(self):
        mock_log = _mock_logger()
        logger = TechnicalLogger(mock_log, component="database")

        logger.operation("db.insert", success=False)

        mock_log.error.assert_called_once()
        call_args = mock_log.error.call_args
        assert call_args[0][0] == "db.insert failed"

    def test_connection_error(self):
        mock_log = _mock_logger()
        logger = TechnicalLogger(mock_log, component="database")
        test_error = ConnectionError("Connection refused")

        logger.connection_error("postgresql", error=test_error, host="localhost", port=5432)

        mock_log.exception.assert_called_once()
        call_args = mock_log.exception.call_args
        assert call_args[0][0] == "Failed to connect to postgresql"
        assert call_args[1]["extra"]["service"] == "postgresql"
        assert call_args[1]["extra"]["error_category"] == "connection"
        assert call_args[1]["extra"]["host"] == "localhost"
        assert call_args[1]["extra"]["port"] == 5432
        assert call_args[1]["extra"]["error_class"] == "ConnectionError"

    def test_timeout(self):
        mock_log = _mock_logger()
        logger = TechnicalLogger(mock_log, component="database")

        logger.timeout("db.query", timeout_ms=5000, query="SELECT *")

        mock_log.error.assert_called_once()
        call_args = mock_log.error.call_args
        assert "timed out" in call_args[0][0]
        assert call_args[1]["extra"]["operation"] == "db.query"
        assert call_args[1]["extra"]["timeout_ms"] == 5000
        assert call_args[1]["extra"]["error_category"] == "timeout"

    def test_slow_operation(self):
        mock_log = _mock_logger()
        logger = TechnicalLogger(mock_log, component="database")

        logger.slow_operation("db.query", duration_ms=2500, threshold_ms=1000, table="projects")

        mock_log.warning.assert_called_once()
        call_args = mock_log.warning.call_args
        assert "Slow operation" in call_args[0][0]
        assert call_args[1]["extra"]["operation"] == "db.query"
        assert call_args[1]["extra"]["duration_ms"] == 2500
        assert call_args[1]["extra"]["threshold_ms"] == 1000
        assert call_args[1]["extra"]["slowdown_factor"] == 2.5


# ---------------------------------------------------------------------------
# IntegrationLogger
# ---------------------------------------------------------------------------


class TestIntegrationLogger:
    """Tests for IntegrationLogger."""

    def test_init_sets_service(self):
        mock_log = _mock_logger()
        logger = IntegrationLogger(mock_log, service_name="openai")

        logger.info("test")

        mock_log.info.assert_called_once_with("test", extra={"service": "openai", "logger_type": "integration"})

    def test_api_call_success(self):
        mock_log = _mock_logger()
        logger = IntegrationLogger(mock_log, service_name="openai")

        logger.api_call(
            "/v1/chat/completions", method="POST", duration_ms=1250, status_code=200, model="gpt-4o", tokens=1500
        )

        mock_log.info.assert_called_once()
        call_args = mock_log.info.call_args
        assert call_args[0][0] == "API call: POST /v1/chat/completions"
        assert call_args[1]["extra"]["endpoint"] == "/v1/chat/completions"
        assert call_args[1]["extra"]["method"] == "POST"
        assert call_args[1]["extra"]["duration_ms"] == 1250
        assert call_args[1]["extra"]["status_code"] == 200
        assert call_args[1]["extra"]["api_call"] is True
        assert call_args[1]["extra"]["service"] == "openai"

    def test_api_call_minimal(self):
        mock_log = _mock_logger()
        logger = IntegrationLogger(mock_log, service_name="openai")

        logger.api_call("/v1/models")

        call_args = mock_log.info.call_args
        assert call_args[1]["extra"]["endpoint"] == "/v1/models"
        assert "duration_ms" not in call_args[1]["extra"]
        assert "status_code" not in call_args[1]["extra"]

    def test_api_error(self):
        mock_log = _mock_logger()
        logger = IntegrationLogger(mock_log, service_name="openai")
        test_error = TimeoutError("Request timed out")

        logger.api_error(
            "/v1/chat/completions", error=test_error, status_code=429, method="POST", model="gpt-4o", retry_after=60
        )

        mock_log.exception.assert_called_once()
        call_args = mock_log.exception.call_args
        assert call_args[0][0] == "API call failed: POST /v1/chat/completions"
        assert call_args[1]["extra"]["endpoint"] == "/v1/chat/completions"
        assert call_args[1]["extra"]["status_code"] == 429
        assert call_args[1]["extra"]["api_error"] is True
        assert call_args[1]["extra"]["retry_after"] == 60
        assert call_args[1]["extra"]["error_class"] == "TimeoutError"

    def test_webhook_success(self):
        mock_log = _mock_logger()
        logger = IntegrationLogger(mock_log, service_name="stripe")

        logger.webhook("payment.succeeded", success=True, payment_id="pay-123", amount=99.99)

        mock_log.info.assert_called_once()
        call_args = mock_log.info.call_args
        assert call_args[0][0] == "Webhook payment.succeeded processed"
        assert call_args[1]["extra"]["webhook"] is True
        assert call_args[1]["extra"]["event_type"] == "payment.succeeded"
        assert call_args[1]["extra"]["success"] is True
        assert call_args[1]["extra"]["amount"] == 99.99

    def test_webhook_failure(self):
        mock_log = _mock_logger()
        logger = IntegrationLogger(mock_log, service_name="stripe")

        logger.webhook("payment.failed", success=False)

        mock_log.error.assert_called_once()
        call_args = mock_log.error.call_args
        assert call_args[0][0] == "Webhook payment.failed failed"


# ---------------------------------------------------------------------------
# ApplicationLogger
# ---------------------------------------------------------------------------


class TestApplicationLogger:
    """Tests for ApplicationLogger."""

    def test_init_with_component(self):
        mock_log = _mock_logger()
        logger = ApplicationLogger(mock_log, component="api")

        logger.info("test")

        mock_log.info.assert_called_once_with("test", extra={"logger_type": "application", "component": "api"})

    def test_init_without_component(self):
        mock_log = _mock_logger()
        logger = ApplicationLogger(mock_log)

        logger.info("test")

        mock_log.info.assert_called_once_with("test", extra={"logger_type": "application"})

    def test_startup(self):
        mock_log = _mock_logger()
        logger = ApplicationLogger(mock_log, component="api")

        logger.startup("Server started", port=8000, workers=4, env="production")

        mock_log.info.assert_called_once()
        call_args = mock_log.info.call_args
        assert "STARTUP:" in call_args[0][0]
        assert call_args[1]["extra"]["port"] == 8000
        assert call_args[1]["extra"]["workers"] == 4
        assert call_args[1]["extra"]["env"] == "production"
        assert call_args[1]["extra"]["event_category"] == "startup"

    def test_shutdown(self):
        mock_log = _mock_logger()
        logger = ApplicationLogger(mock_log, component="api")

        logger.shutdown("Server stopping", reason="SIGTERM")

        mock_log.warning.assert_called_once()
        call_args = mock_log.warning.call_args
        assert "SHUTDOWN:" in call_args[0][0]
        assert call_args[1]["extra"]["event_category"] == "shutdown"
        assert call_args[1]["extra"]["reason"] == "SIGTERM"

    def test_config_loaded(self):
        mock_log = _mock_logger()
        logger = ApplicationLogger(mock_log, component="config")

        logger.config_loaded("config_prod.yml", env="production")

        mock_log.info.assert_called_once()
        call_args = mock_log.info.call_args
        assert "Configuration loaded" in call_args[0][0]
        assert call_args[1]["extra"]["config_source"] == "config_prod.yml"

    def test_migration_success(self):
        mock_log = _mock_logger()
        logger = ApplicationLogger(mock_log, component="migrations")

        logger.migration("upgrade", success=True, duration_ms=1250)

        mock_log.info.assert_called_once()
        call_args = mock_log.info.call_args
        assert "succeeded" in call_args[0][0]
        assert call_args[1]["extra"]["success"] is True
        assert call_args[1]["extra"]["migration_action"] == "upgrade"

    def test_migration_failure(self):
        mock_log = _mock_logger()
        logger = ApplicationLogger(mock_log, component="migrations")

        logger.migration("upgrade", success=False)

        mock_log.error.assert_called_once()
        call_args = mock_log.error.call_args
        assert "failed" in call_args[0][0]

    def test_feature_flag(self):
        mock_log = _mock_logger()
        logger = ApplicationLogger(mock_log, component="api")

        logger.feature_flag("new_ui_enabled", enabled=True)

        mock_log.debug.assert_called_once()
        call_args = mock_log.debug.call_args
        assert "new_ui_enabled" in call_args[0][0]
        assert call_args[1]["extra"]["enabled"] is True
        assert call_args[1]["extra"]["flag_name"] == "new_ui_enabled"
