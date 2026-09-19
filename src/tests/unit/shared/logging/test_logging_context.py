"""Tests for logging context vars and the _ContextFilter injection."""

import logging

import pytest

from src.app.shared.logging.logging import (
    _ContextFilter,
    _request_id_ctx,
    _user_id_ctx,
    clear_context,
    set_request_id,
    set_user_id,
)


def _make_record(msg: str = "test message", level: int = logging.INFO) -> logging.LogRecord:
    return logging.LogRecord(
        name="test",
        level=level,
        pathname="",
        lineno=0,
        msg=msg,
        args=(),
        exc_info=None,
    )


@pytest.fixture(autouse=True)
def _isolate_context():
    """Reset context vars around every test."""
    token_r = _request_id_ctx.set("-")
    token_u = _user_id_ctx.set("-")
    try:
        yield
    finally:
        _request_id_ctx.reset(token_r)
        _user_id_ctx.reset(token_u)


class TestSetRequestId:
    def test_sets_value(self):
        set_request_id("req-123")
        assert _request_id_ctx.get() == "req-123"

    def test_none_sets_dash(self):
        set_request_id("req-123")
        set_request_id(None)
        assert _request_id_ctx.get() == "-"

    def test_empty_string_sets_dash(self):
        set_request_id("")
        assert _request_id_ctx.get() == "-"


class TestSetUserId:
    def test_sets_value(self):
        set_user_id("user-456")
        assert _user_id_ctx.get() == "user-456"

    def test_none_sets_dash(self):
        set_user_id("user-456")
        set_user_id(None)
        assert _user_id_ctx.get() == "-"

    def test_empty_string_sets_dash(self):
        set_user_id("")
        assert _user_id_ctx.get() == "-"


class TestClearContext:
    def test_resets_both_vars(self):
        set_request_id("req-123")
        set_user_id("user-456")

        clear_context()

        assert _request_id_ctx.get() == "-"
        assert _user_id_ctx.get() == "-"

    def test_clear_when_already_default_is_noop(self):
        clear_context()
        assert _request_id_ctx.get() == "-"
        assert _user_id_ctx.get() == "-"


class TestContextFilter:
    def test_filter_returns_true(self):
        assert _ContextFilter().filter(_make_record()) is True

    def test_injects_request_id(self):
        set_request_id("req-abc")
        record = _make_record()
        _ContextFilter().filter(record)
        assert record.request_id == "req-abc"

    def test_injects_user_id(self):
        set_user_id("user-xyz")
        record = _make_record()
        _ContextFilter().filter(record)
        assert record.user_id == "user-xyz"

    def test_defaults_to_dash(self):
        record = _make_record()
        _ContextFilter().filter(record)
        assert record.request_id == "-"
        assert record.user_id == "-"

    def test_injects_both_context_values(self):
        set_request_id("req-1")
        set_user_id("user-1")
        record = _make_record()
        _ContextFilter().filter(record)
        assert record.request_id == "req-1"
        assert record.user_id == "user-1"
