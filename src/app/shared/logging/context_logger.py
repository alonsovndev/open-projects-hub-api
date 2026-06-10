"""Context-aware logging foundation."""

from logging import Logger
from typing import Any


class ContextLogger:
    """
    Base context-aware logger that wraps standard logger.
    Automatically includes context in all log calls.
    """

    def __init__(self, logger: Logger, context: dict[str, Any] | None = None):
        """
        Initialize with logger and optional context.

        Args:
            logger: Standard Python logger instance
            context: Context dict to include in all logs (user_id, request_id, etc.)
        """
        self._logger = logger
        self._context = context or {}

    def with_context(self, **kwargs: Any) -> "ContextLogger":
        """
        Return new logger with additional context merged.

        Example:
            log = base_log.with_context(request_id="req-123")
        """
        merged = {**self._context, **kwargs}
        return ContextLogger(self._logger, merged)

    def _merge_extra(self, **extra: Any) -> dict[str, Any]:
        """Merge context with additional data."""
        return {**self._context, **extra}

    def info(self, message: str, **extra: Any) -> None:
        """Log info message with context."""
        self._logger.info(message, extra=self._merge_extra(**extra))

    def error(self, message: str, error: Exception | None = None, **extra: Any) -> None:
        """
        Log error message with context and optional exception.

        Args:
            message: Error message
            error: Exception instance (will include traceback)
            **extra: Additional structured data
        """
        merged_extra = self._merge_extra(**extra)

        if error:
            merged_extra["error_class"] = type(error).__name__
            merged_extra["error_message"] = str(error)
            self._logger.exception(message, extra=merged_extra)
        else:
            self._logger.error(message, extra=merged_extra)

    def warning(self, message: str, **extra: Any) -> None:
        """Log warning message with context."""
        self._logger.warning(message, extra=self._merge_extra(**extra))

    def debug(self, message: str, **extra: Any) -> None:
        """Log debug message with context."""
        self._logger.debug(message, extra=self._merge_extra(**extra))
