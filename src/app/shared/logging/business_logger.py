"""Business operation logging."""

from logging import Logger
from typing import Any

from src.app.shared.logging.context_logger import ContextLogger
from src.app.shared.logging.utils import redact_sensitive_fields


class BusinessLogger(ContextLogger):
    """
    Logger for business domain operations.
    Requires user_id context and provides domain event methods.
    """

    def __init__(self, logger: Logger, user_id: str):
        """
        Initialize business logger with user context.

        Args:
            logger: Standard Python logger
            user_id: User ID performing the operation (from JWT)
        """
        super().__init__(logger, context={"user_id": user_id, "logger_type": "business"})

    def event(self, event_type: str, entity_id: str | None = None, message: str | None = None, **data: Any) -> None:
        """
        Log successful business event.

        Args:
            event_type: Event type (e.g., "project.created", "story.assigned")
            entity_id: Entity ID if applicable
            message: Custom message, auto-generated from event_type if None
            **data: Additional structured data (project_name, client_id, etc.)

        Example:
            log.event("project.created", entity_id="proj-123",
                     project_name="My Project", client_id="client-456")
        """
        msg = message or self._generate_message(event_type)
        extra: dict[str, Any] = {"event_type": event_type}

        if entity_id:
            extra["entity_id"] = entity_id

        if data:
            extra.update(redact_sensitive_fields(data))

        self.info(msg, **extra)

    def failure(
        self,
        error_type: str,
        error: Exception | None = None,
        entity_id: str | None = None,
        message: str | None = None,
        **data: Any,
    ) -> None:
        """
        Log business operation failure.

        Args:
            error_type: Error type (e.g., "project.create.failed", "story.not_found")
            error: Exception instance if available
            entity_id: Entity ID if applicable
            message: Custom error message
            **data: Additional context data

        Example:
            log.failure("project.create.client_not_found",
                       client_id=request.client_id)
        """
        msg = message or self._generate_message(error_type)
        extra: dict[str, Any] = {"error_type": error_type}

        if entity_id:
            extra["entity_id"] = entity_id

        if data:
            extra.update(redact_sensitive_fields(data))

        self.error(msg, error=error, **extra)

    @staticmethod
    def _generate_message(event_or_error_type: str) -> str:
        """Generate human-readable message from event/error type."""
        return event_or_error_type.replace(".", " ").replace("_", " ").title()
