"""Technical and infrastructure logging."""

from logging import Logger
from typing import Any

from src.app.shared.logging.context_logger import ContextLogger


class TechnicalLogger(ContextLogger):
    """
    Logger for technical/infrastructure operations.
    No user context required. For database, cache, file system, etc.
    """

    def __init__(self, logger: Logger, component: str):
        """
        Initialize technical logger with component context.

        Args:
            logger: Standard Python logger
            component: Component name (e.g., "database", "cache", "filesystem")
        """
        super().__init__(logger, context={"component": component, "logger_type": "technical"})

    def operation(self, operation: str, success: bool = True, duration_ms: float | None = None, **data: Any) -> None:
        """
        Log technical operation (query, cache access, file read).

        Args:
            operation: Operation name (e.g., "db.query", "cache.get", "file.read")
            success: Whether operation succeeded
            duration_ms: Operation duration in milliseconds
            **data: Additional data (table, key, path, rows_affected, etc.)

        Example:
            tech_log.operation("db.insert", success=True, duration_ms=45.2,
                              table="projects", rows_affected=1)
        """
        extra: dict[str, Any] = {"operation": operation, "success": success}

        if duration_ms is not None:
            extra["duration_ms"] = duration_ms

        if data:
            extra.update(data)

        msg = f"{operation} {'succeeded' if success else 'failed'}"

        if success:
            self.info(msg, **extra)
        else:
            self.error(msg, **extra)

    def connection_error(self, service: str, error: Exception, **data: Any) -> None:
        """
        Log connection failure to infrastructure service.

        Args:
            service: Service name (e.g., "postgresql", "redis", "s3")
            error: Connection exception
            **data: Connection details (host, port, database, etc.)

        Example:
            tech_log.connection_error("postgresql", error=e,
                                     host="localhost", port=5432, database="app_db")
        """
        self.error(f"Failed to connect to {service}", error=error, service=service, error_category="connection", **data)

    def timeout(self, operation: str, timeout_ms: float, **data: Any) -> None:
        """
        Log operation timeout.

        Args:
            operation: Operation that timed out
            timeout_ms: Timeout threshold in milliseconds
            **data: Additional context

        Example:
            tech_log.timeout("db.query", timeout_ms=5000,
                            query="SELECT * FROM projects WHERE...")
        """
        self.error(
            f"Operation timed out: {operation}",
            operation=operation,
            timeout_ms=timeout_ms,
            error_category="timeout",
            **data,
        )

    def slow_operation(self, operation: str, duration_ms: float, threshold_ms: float, **data: Any) -> None:
        """
        Log slow operation warning.

        Args:
            operation: Operation name
            duration_ms: Actual duration
            threshold_ms: Expected threshold
            **data: Additional context

        Example:
            tech_log.slow_operation("db.query", duration_ms=2500, threshold_ms=1000,
                                   table="projects", query_type="full_scan")
        """
        self.warning(
            f"Slow operation detected: {operation}",
            operation=operation,
            duration_ms=duration_ms,
            threshold_ms=threshold_ms,
            slowdown_factor=round(duration_ms / threshold_ms, 2),
            **data,
        )
