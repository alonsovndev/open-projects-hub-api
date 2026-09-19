"""Simplified structured logging with request/user correlation.

Lower environments (local, test, container) use plain-text output for
readability. Higher environments (dev, prod) use single-line JSON for
log aggregation. Request ID and user ID are injected via context
variables so all log lines for a request are correlated.
"""

import json
import logging
import sys
from contextvars import ContextVar
from datetime import UTC, datetime


_request_id_ctx: ContextVar[str] = ContextVar("request_id", default="-")
_user_id_ctx: ContextVar[str] = ContextVar("user_id", default="-")

_configured = False

STANDARD_RECORD_KEYS = frozenset(
    {
        "name",
        "msg",
        "args",
        "levelname",
        "levelno",
        "pathname",
        "filename",
        "module",
        "exc_info",
        "exc_text",
        "stack_info",
        "lineno",
        "funcName",
        "created",
        "msecs",
        "relativeCreated",
        "thread",
        "threadName",
        "processName",
        "process",
        "taskName",
        "request_id",
        "user_id",
        "message",
    }
)


def set_request_id(request_id: str | None) -> None:
    """Set the request correlation ID. Called by middleware."""
    _request_id_ctx.set(request_id or "-")


def set_user_id(user_id: str | None) -> None:
    """Set the authenticated user ID. Called by middleware or use cases."""
    _user_id_ctx.set(user_id or "-")


def clear_context() -> None:
    """Reset both context vars to '-'. Called by middleware after request."""
    _request_id_ctx.set("-")
    _user_id_ctx.set("-")


class _ContextFilter(logging.Filter):
    """Inject request_id and user_id from context vars into every record."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = _request_id_ctx.get()
        record.user_id = _user_id_ctx.get()
        return True


class _JsonFormatter(logging.Formatter):
    """Render a log record as a single-line JSON object."""

    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "request_id": getattr(record, "request_id", "-"),
            "user_id": getattr(record, "user_id", "-"),
            "message": record.getMessage(),
        }
        for key, value in record.__dict__.items():
            if key not in STANDARD_RECORD_KEYS and not key.startswith("_"):
                payload[key] = value
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, default=str)


class _PlainFormatter(logging.Formatter):
    """Render a log record as a human-readable single line for local/dev runs."""

    def format(self, record: logging.LogRecord) -> str:
        timestamp = datetime.fromtimestamp(record.created, tz=UTC).strftime("%H:%M:%S")
        context_parts = []
        rid = getattr(record, "request_id", "-")
        uid = getattr(record, "user_id", "-")
        if rid != "-":
            context_parts.append(f"req={rid}")
        if uid != "-":
            context_parts.append(f"user={uid}")
        context = f"[{' '.join(context_parts)}] " if context_parts else ""
        line = f"{timestamp} [{record.levelname:<5}] {context}{record.name} — {record.getMessage()}"
        extras = {k: v for k, v in record.__dict__.items() if k not in STANDARD_RECORD_KEYS and not k.startswith("_")}
        if extras:
            line += f"  {extras}"
        if record.exc_info:
            line += "\n" + self.formatException(record.exc_info)
        return line


def _resolve_level(level: str | int) -> int:
    if isinstance(level, str):
        return getattr(logging, level.upper(), logging.INFO)
    return level


def setup_logging(level: str | int = logging.INFO, plain_text: bool = False) -> None:
    """One-call bootstrap. Clears existing handlers, installs a single
    StreamHandler(sys.stdout) with _ContextFilter + formatter, sets root level.
    Idempotent: re-invocation updates level and format without re-adding handlers.
    """
    global _configured

    handler = logging.StreamHandler(sys.stdout)
    handler.addFilter(_ContextFilter())
    handler.setFormatter(_PlainFormatter() if plain_text else _JsonFormatter())

    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(_resolve_level(level))
    _configured = True


def get_logger(name: str) -> logging.Logger:
    """Return a standard logging.Logger. Ensures root is configured."""
    if not _configured:
        setup_logging()
    return logging.getLogger(name)
