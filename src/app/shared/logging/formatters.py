"""Log formatters: JSON and plain text."""

import logging

from pythonjsonlogger.json import JsonFormatter as BaseJsonFormatter


class JsonFormatter(BaseJsonFormatter):
    """JSON formatter with standard observability fields."""

    def add_fields(self, log_record, record, message_dict):
        super().add_fields(log_record, record, message_dict)
        log_record["timestamp"] = record.created
        log_record["level"] = record.levelname
        log_record["logger"] = record.name
        if record.pathname:
            log_record["module"] = record.module
        if record.funcName:
            log_record["function"] = record.funcName


class TextFormatter(logging.Formatter):
    """Plain text formatter for human-readable output."""

    def __init__(self):
        super().__init__(
            fmt="%(levelname)s %(asctime)s [%(request_id)s] [user:%(user_id)s] %(name)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
            defaults={"request_id": "N/A", "user_id": "anonymous"},
        )
