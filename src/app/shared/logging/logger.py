"""Logger setup and factory."""

import logging

from src.app.shared.logging.config import LoggingConfig
from src.app.shared.logging.correlation import CorrelationIdFilter
from src.app.shared.logging.handlers import create_console_handler, create_file_handler


_LOGGING_INITIALIZED = False


def setup_logging(config: LoggingConfig) -> None:
    """Configure the root logger once at app startup.

    Creates handlers for each output type defined in config,
    attaches CorrelationIdFilter to all handlers.
    """
    global _LOGGING_INITIALIZED
    if _LOGGING_INITIALIZED:
        return

    root = logging.getLogger()
    root.setLevel(config.level.upper())

    # Clear any existing handlers (e.g. from test runners)
    root.handlers.clear()

    # Add correlation ID filter to root so every handler gets request_id
    root.addFilter(CorrelationIdFilter())

    for output in config.outputs:
        if output.type == "console":
            handler = create_console_handler(config.level, config.format)
            root.addHandler(handler)
        elif output.type == "file":
            if output.path:
                handler = create_file_handler(
                    level=config.level,
                    fmt=config.format,
                    path=output.path,
                    max_bytes=output.max_bytes or 52428800,
                    backup_count=output.backup_count or 5,
                )
                root.addHandler(handler)

    _LOGGING_INITIALIZED = True


def get_logger(name: str) -> logging.Logger:
    """Return a named logger. Call setup_logging() first at app startup."""
    return logging.getLogger(name)
