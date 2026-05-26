"""Log handler factories: console and file with rotation."""

import logging
import os
from logging.handlers import RotatingFileHandler

from src.app.shared.logging.formatters import JsonFormatter, TextFormatter


def _make_formatter(fmt: str) -> logging.Formatter:
    if fmt == "json":
        return JsonFormatter("%(timestamp)s %(level)s %(logger)s %(message)s")
    return TextFormatter()


def create_console_handler(level: str, fmt: str) -> logging.Handler:
    """Create a StreamHandler writing to stdout."""
    handler = logging.StreamHandler()
    handler.setLevel(level.upper())
    handler.setFormatter(_make_formatter(fmt))
    return handler


def create_file_handler(
    level: str,
    fmt: str,
    path: str,
    max_bytes: int = 52428800,
    backup_count: int = 5,
) -> logging.Handler:
    """Create a RotatingFileHandler with the given path and rotation settings."""
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    handler = RotatingFileHandler(
        path,
        maxBytes=max_bytes,
        backupCount=backup_count,
    )
    handler.setLevel(level.upper())
    handler.setFormatter(_make_formatter(fmt))
    return handler
