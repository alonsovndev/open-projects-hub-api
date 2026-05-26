"""Shared logging module: config-driven handlers, correlation IDs, structured output."""

from src.app.shared.logging.config import LoggingConfig, load_logging_config
from src.app.shared.logging.correlation import CorrelationIdMiddleware
from src.app.shared.logging.logger import get_logger, setup_logging


__all__ = [
    "CorrelationIdMiddleware",
    "LoggingConfig",
    "get_logger",
    "load_logging_config",
    "setup_logging",
]
