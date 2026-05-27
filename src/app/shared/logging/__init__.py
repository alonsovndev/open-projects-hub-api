"""Shared logging module: config-driven handlers, correlation IDs, structured output."""

from src.app.shared.logging.config import LoggingConfig, load_logging_config
from src.app.shared.logging.correlation import CorrelationIdMiddleware, set_user_context
from src.app.shared.logging.logger import get_logger, setup_logging
from src.app.shared.logging.utils import log_business_event, log_error_event, mask_email, redact_sensitive_fields


__all__ = [
    "CorrelationIdMiddleware",
    "LoggingConfig",
    "get_logger",
    "load_logging_config",
    "log_business_event",
    "log_error_event",
    "mask_email",
    "redact_sensitive_fields",
    "set_user_context",
    "setup_logging",
]
