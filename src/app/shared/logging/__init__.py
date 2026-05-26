"""Shared logging module: config-driven handlers, correlation IDs, structured output."""

from src.app.shared.logging.config import LoggingConfig, load_logging_config
from src.app.shared.logging.logger import setup_logging, get_logger
from src.app.shared.logging.correlation import CorrelationIdMiddleware

__all__ = [
    "LoggingConfig",
    "load_logging_config",
    "setup_logging",
    "get_logger",
    "CorrelationIdMiddleware",
]
