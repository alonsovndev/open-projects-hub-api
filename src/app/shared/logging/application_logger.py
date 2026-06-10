"""General application logging."""

from logging import Logger
from typing import Any

from src.app.shared.logging.context_logger import ContextLogger


class ApplicationLogger(ContextLogger):
    """
    Default logger for general application events.
    Use when business/technical/integration loggers don't apply.
    """

    def __init__(self, logger: Logger, component: str | None = None):
        """
        Initialize application logger.

        Args:
            logger: Standard Python logger
            component: Optional component name for categorization
        """
        context: dict[str, Any] = {"logger_type": "application"}
        if component:
            context["component"] = component
        super().__init__(logger, context=context)

    def startup(self, message: str, **data: Any) -> None:
        """
        Log application startup event.

        Example:
            app_log.startup("API server started", port=8000, workers=4, env="production")
        """
        self.info(f"STARTUP: {message}", event_category="startup", **data)

    def shutdown(self, message: str, **data: Any) -> None:
        """
        Log application shutdown event.

        Example:
            app_log.shutdown("API server stopping", reason="SIGTERM", active_requests=3)
        """
        self.warning(f"SHUTDOWN: {message}", event_category="shutdown", **data)

    def config_loaded(self, config_source: str, **data: Any) -> None:
        """
        Log configuration loaded.

        Example:
            app_log.config_loaded("config_prod.yml", settings_count=42, env="production")
        """
        self.info(
            f"Configuration loaded from {config_source}", event_category="config", config_source=config_source, **data
        )

    def migration(self, action: str, success: bool = True, **data: Any) -> None:
        """
        Log database migration event.

        Example:
            app_log.migration("upgrade", success=True, target_revision="abc123", duration_ms=1250)
        """
        msg = f"Database migration {action} {'succeeded' if success else 'failed'}"
        extra: dict[str, Any] = {"event_category": "migration", "migration_action": action, "success": success}
        extra.update(data)

        if success:
            self.info(msg, **extra)
        else:
            self.error(msg, **extra)

    def feature_flag(self, flag_name: str, enabled: bool, **data: Any) -> None:
        """
        Log feature flag evaluation.

        Example:
            app_log.feature_flag("new_ui_enabled", enabled=True, user_id="user-123")
        """
        status = "enabled" if enabled else "disabled"
        self.debug(
            f"Feature flag '{flag_name}': {status}",
            event_category="feature_flag",
            flag_name=flag_name,
            enabled=enabled,
            **data,
        )
