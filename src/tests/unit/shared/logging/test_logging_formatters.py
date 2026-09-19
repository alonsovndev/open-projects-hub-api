"""Tests for JSON and plain text formatters, _resolve_level, and setup_logging."""

import json
import logging
import sys

import pytest

from src.app.shared.logging.logging import (
    _ContextFilter,
    _JsonFormatter,
    _PlainFormatter,
    _resolve_level,
    get_logger,
    setup_logging,
)


def _make_record(msg: str = "test message", level: int = logging.INFO) -> logging.LogRecord:
    record = logging.LogRecord(
        name="test.logger",
        level=level,
        pathname="",
        lineno=0,
        msg=msg,
        args=(),
        exc_info=None,
    )
    _ContextFilter().filter(record)
    return record


@pytest.fixture(autouse=True)
def _restore_root_logger():
    """Restore root logger handlers/level after each test so setup_logging stays idempotent."""
    root = logging.getLogger()
    saved_handlers = list(root.handlers)
    saved_level = root.level
    # Reset the module-level _configured flag so setup_logging re-runs fresh each test
    from src.app.shared.logging import logging as logging_module

    configured_flag = logging_module._configured
    logging_module._configured = False
    try:
        yield
    finally:
        logging_module._configured = configured_flag
        root.handlers = saved_handlers
        root.setLevel(saved_level)


class TestJsonFormatter:
    def test_produces_valid_json(self):
        output = _JsonFormatter().format(_make_record("hello"))
        parsed = json.loads(output)
        assert parsed["message"] == "hello"
        assert parsed["level"] == "INFO"
        assert parsed["logger"] == "test.logger"
        assert "timestamp" in parsed
        assert parsed["request_id"] == "-"
        assert parsed["user_id"] == "-"

    def test_includes_request_and_user_context(self):
        from src.app.shared.logging.logging import set_request_id, set_user_id

        set_request_id("req-abc")
        set_user_id("user-xyz")
        try:
            output = _JsonFormatter().format(_make_record("ctx"))
            parsed = json.loads(output)
            assert parsed["request_id"] == "req-abc"
            assert parsed["user_id"] == "user-xyz"
        finally:
            set_request_id(None)
            set_user_id(None)

    def test_includes_extra_fields(self):
        record = _make_record("created")
        record.entity_id = "proj-123"
        record.event_type = "project.created"
        parsed = json.loads(_JsonFormatter().format(record))
        assert parsed["entity_id"] == "proj-123"
        assert parsed["event_type"] == "project.created"

    def test_exception_included_when_exc_info(self):
        try:
            raise ValueError("boom")
        except ValueError:
            import sys

            record = logging.LogRecord(
                name="test",
                level=logging.ERROR,
                pathname="",
                lineno=0,
                msg="error",
                args=(),
                exc_info=sys.exc_info(),
            )
        _ContextFilter().filter(record)
        parsed = json.loads(_JsonFormatter().format(record))
        assert "exception" in parsed
        assert "ValueError" in parsed["exception"]


class TestPlainFormatter:
    def test_produces_readable_line(self):
        output = _PlainFormatter().format(_make_record("hello world"))
        assert "hello world" in output
        assert "INFO" in output

    def test_no_context_shown_when_dash(self):
        output = _PlainFormatter().format(_make_record("test"))
        assert "req=" not in output
        assert "user=" not in output

    def test_shows_context_when_set(self):
        from src.app.shared.logging.logging import set_request_id, set_user_id

        set_request_id("req-1")
        set_user_id("user-1")
        try:
            output = _PlainFormatter().format(_make_record("ctx"))
            assert "req=req-1" in output
            assert "user=user-1" in output
        finally:
            set_request_id(None)
            set_user_id(None)

    def test_shows_extras(self):
        record = _make_record("created")
        record.entity_id = "proj-123"
        output = _PlainFormatter().format(record)
        assert "entity_id" in output
        assert "proj-123" in output

    def test_exception_included_when_exc_info(self):
        try:
            raise RuntimeError("kaboom")
        except RuntimeError:
            import sys

            record = logging.LogRecord(
                name="test",
                level=logging.ERROR,
                pathname="",
                lineno=0,
                msg="error",
                args=(),
                exc_info=sys.exc_info(),
            )
        _ContextFilter().filter(record)
        output = _PlainFormatter().format(record)
        assert "RuntimeError" in output
        assert "kaboom" in output


class TestResolveLevel:
    def test_string_level_uppercased(self):
        assert _resolve_level("debug") == logging.DEBUG
        assert _resolve_level("INFO") == logging.INFO
        assert _resolve_level("warning") == logging.WARNING

    def test_int_level_returned_as_is(self):
        assert _resolve_level(logging.ERROR) == logging.ERROR

    def test_unknown_string_falls_back_to_info(self):
        assert _resolve_level("nonexistent") == logging.INFO


class TestSetupLogging:
    def test_installs_single_stdout_handler(self):
        setup_logging(level="INFO", plain_text=True)
        root = logging.getLogger()
        assert len(root.handlers) == 1
        assert isinstance(root.handlers[0], logging.StreamHandler)
        assert root.handlers[0].stream is sys.stdout

    def test_sets_root_level_string(self):
        setup_logging(level="DEBUG")
        assert logging.getLogger().level == logging.DEBUG

    def test_sets_root_level_int(self):
        setup_logging(level=logging.WARNING)
        assert logging.getLogger().level == logging.WARNING

    def test_uses_plain_formatter_when_plain_text(self):
        setup_logging(level="INFO", plain_text=True)
        assert isinstance(logging.getLogger().handlers[0].formatter, _PlainFormatter)

    def test_uses_json_formatter_by_default(self):
        setup_logging(level="INFO")
        assert isinstance(logging.getLogger().handlers[0].formatter, _JsonFormatter)

    def test_clears_existing_handlers(self):
        root = logging.getLogger()
        # Add a fake handler that should be cleared
        fake = logging.NullHandler()
        root.addHandler(fake)
        setup_logging(level="INFO")
        assert fake not in root.handlers

    def test_handler_has_context_filter(self):
        setup_logging(level="INFO")
        handler = logging.getLogger().handlers[0]
        filters = handler.filters
        assert any(isinstance(f, _ContextFilter) for f in filters)


class TestGetLogger:
    def test_returns_logger_by_name(self):
        log = get_logger("my.module")
        assert isinstance(log, logging.Logger)
        assert log.name == "my.module"

    def test_first_call_triggers_setup(self):
        get_logger("auto.configure")
        root = logging.getLogger()
        # setup_logging should have configured at least one handler
        assert len(root.handlers) >= 1
