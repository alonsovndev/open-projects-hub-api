"""External service integration logging."""

from logging import Logger
from typing import Any

from src.app.shared.logging.context_logger import ContextLogger
from src.app.shared.logging.utils import redact_sensitive_fields


class IntegrationLogger(ContextLogger):
    """
    Logger for external service integrations.
    For API calls, webhooks, third-party services.
    """

    def __init__(self, logger: Logger, service_name: str):
        """
        Initialize integration logger with service context.

        Args:
            logger: Standard Python logger
            service_name: External service name (e.g., "openai", "stripe", "sendgrid")
        """
        super().__init__(logger, context={"service": service_name, "logger_type": "integration"})

    def api_call(
        self,
        endpoint: str,
        method: str = "POST",
        duration_ms: float | None = None,
        status_code: int | None = None,
        **data: Any,
    ) -> None:
        """
        Log external API call.

        Args:
            endpoint: API endpoint (e.g., "/v1/chat/completions")
            method: HTTP method
            duration_ms: Request duration
            status_code: HTTP status code
            **data: Additional data (request_id, params, response_size, etc.)

        Example:
            int_log.api_call("/v1/chat/completions", method="POST",
                           duration_ms=1250, status_code=200,
                           model="gpt-4o", tokens=1500)
        """
        extra: dict[str, Any] = {
            "endpoint": endpoint,
            "method": method,
            "api_call": True,
        }

        if duration_ms is not None:
            extra["duration_ms"] = duration_ms

        if status_code is not None:
            extra["status_code"] = status_code

        if data:
            extra.update(redact_sensitive_fields(data))

        msg = f"API call: {method} {endpoint}"
        self.info(msg, **extra)

    def api_error(
        self, endpoint: str, error: Exception, status_code: int | None = None, method: str = "POST", **data: Any
    ) -> None:
        """
        Log API call failure.

        Args:
            endpoint: API endpoint
            error: Exception raised
            status_code: HTTP status code if available
            method: HTTP method
            **data: Additional error context

        Example:
            int_log.api_error("/v1/chat/completions", error=e,
                            status_code=429, method="POST",
                            model="gpt-4o", retry_after=60)
        """
        extra: dict[str, Any] = {
            "endpoint": endpoint,
            "method": method,
            "api_call": True,
            "api_error": True,
        }

        if status_code is not None:
            extra["status_code"] = status_code

        if data:
            extra.update(redact_sensitive_fields(data))

        msg = f"API call failed: {method} {endpoint}"
        self.error(msg, error=error, **extra)

    def webhook(self, event_type: str, success: bool = True, **data: Any) -> None:
        """
        Log webhook received or sent.

        Args:
            event_type: Webhook event type
            success: Whether processing succeeded
            **data: Webhook payload metadata

        Example:
            int_log.webhook("payment.succeeded", success=True,
                          payment_id="pay-123", amount=99.99)
        """
        extra: dict[str, Any] = {"webhook": True, "event_type": event_type, "success": success}

        if data:
            extra.update(redact_sensitive_fields(data))

        msg = f"Webhook {event_type} {'processed' if success else 'failed'}"

        if success:
            self.info(msg, **extra)
        else:
            self.error(msg, **extra)
