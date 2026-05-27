"""Tests for correlation context with user tracking."""

import logging

from src.app.shared.logging.correlation import CorrelationIdFilter, correlation_id, set_user_context, user_id


class TestCorrelationIdFilter:
    """Tests for CorrelationIdFilter with user context support."""

    def test_adds_request_id_to_log_record(self):
        """Test that request_id is added to log record."""
        # Set correlation ID
        token = correlation_id.set("test-request-123")

        try:
            log_filter = CorrelationIdFilter()
            record = logging.LogRecord(
                name="test",
                level=logging.INFO,
                pathname="",
                lineno=0,
                msg="test message",
                args=(),
                exc_info=None,
            )

            result = log_filter.filter(record)

            assert result is True
            assert record.request_id == "test-request-123"
        finally:
            correlation_id.reset(token)

    def test_adds_user_id_to_log_record(self):
        """Test that user_id is added to log record."""
        # Set user context
        token = user_id.set("user-456")

        try:
            log_filter = CorrelationIdFilter()
            record = logging.LogRecord(
                name="test",
                level=logging.INFO,
                pathname="",
                lineno=0,
                msg="test message",
                args=(),
                exc_info=None,
            )

            result = log_filter.filter(record)

            assert result is True
            assert record.user_id == "user-456"
        finally:
            user_id.reset(token)

    def test_defaults_to_na_for_missing_request_id(self):
        """Test that missing request_id defaults to 'N/A'."""
        log_filter = CorrelationIdFilter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="test message",
            args=(),
            exc_info=None,
        )

        result = log_filter.filter(record)

        assert result is True
        assert record.request_id == "N/A"

    def test_defaults_to_anonymous_for_missing_user_id(self):
        """Test that missing user_id defaults to 'anonymous'."""
        log_filter = CorrelationIdFilter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="test message",
            args=(),
            exc_info=None,
        )

        result = log_filter.filter(record)

        assert result is True
        assert record.user_id == "anonymous"


class TestSetUserContext:
    """Tests for set_user_context function."""

    def test_sets_user_id_in_context(self):
        """Test that set_user_context sets the user_id contextvar."""
        set_user_context("user-789")

        try:
            assert user_id.get() == "user-789"
        finally:
            # Clean up
            user_id.set("")

    def test_sets_anonymous_for_none_user_id(self):
        """Test that None user_id sets 'anonymous'."""
        set_user_context(None)

        try:
            assert user_id.get() == "anonymous"
        finally:
            user_id.set("")

    def test_overwrites_previous_user_id(self):
        """Test that setting user context overwrites previous value."""
        set_user_context("user-123")
        assert user_id.get() == "user-123"

        set_user_context("user-456")
        assert user_id.get() == "user-456"

        # Clean up
        user_id.set("")

    def test_context_isolation_between_calls(self):
        """Test that user context is isolated per contextvar token."""
        # This simulates different request contexts
        token1 = user_id.set("user-aaa")

        try:
            assert user_id.get() == "user-aaa"

            # Simulate nested context
            token2 = user_id.set("user-bbb")
            try:
                assert user_id.get() == "user-bbb"
            finally:
                user_id.reset(token2)

            # Should return to previous context
            assert user_id.get() == "user-aaa"
        finally:
            user_id.reset(token1)
