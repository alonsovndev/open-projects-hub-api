"""Shared logging module: config-driven handlers, correlation IDs, structured output."""

from src.app.shared.logging.application_logger import ApplicationLogger
from src.app.shared.logging.business_logger import BusinessLogger
from src.app.shared.logging.config import LoggingConfig, load_logging_config
from src.app.shared.logging.context_logger import ContextLogger
from src.app.shared.logging.correlation import CorrelationIdMiddleware, set_user_context
from src.app.shared.logging.integration_logger import IntegrationLogger
from src.app.shared.logging.logger import get_logger, setup_logging
from src.app.shared.logging.technical_logger import TechnicalLogger
from src.app.shared.logging.utils import mask_email, redact_sensitive_fields


__all__ = [
    "ApplicationLogger",
    "BusinessLogger",
    "ContextLogger",
    "CorrelationIdMiddleware",
    "IntegrationLogger",
    "LoggingConfig",
    "TechnicalLogger",
    "get_logger",
    "load_logging_config",
    "mask_email",
    "redact_sensitive_fields",
    "set_user_context",
    "setup_logging",
]
