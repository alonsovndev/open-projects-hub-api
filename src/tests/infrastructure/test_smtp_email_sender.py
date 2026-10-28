"""Tests for the headers SmtpEmailSender puts on outgoing messages."""

from unittest.mock import AsyncMock

import pytest

from src.app.shared.infrastructure.email import smtp_email_sender
from src.app.shared.infrastructure.email.smtp_email_sender import SmtpEmailSender


@pytest.fixture
def send_mock(monkeypatch):
    mock = AsyncMock()
    monkeypatch.setattr(smtp_email_sender.aiosmtplib, "send", mock)
    return mock


async def test_message_has_from_and_date_headers(send_mock):
    sender = SmtpEmailSender(
        "smtp.resend.com", 587, "resend", "re_secret", "Open Projects Hub <no-reply@send.example.com>"
    )

    await sender.send("user@example.org", "Verify your email", "ABC234")

    message = send_mock.await_args.args[0]
    assert message["From"] == "Open Projects Hub <no-reply@send.example.com>"
    assert message["Date"]


@pytest.fixture
def no_backoff_sleep(monkeypatch):
    monkeypatch.setattr("backoff._async.asyncio.sleep", AsyncMock())


def build_sender() -> SmtpEmailSender:
    return SmtpEmailSender("smtp.resend.com", 587, "resend", "re_secret", "no-reply@send.example.com")


async def test_a_transient_connection_failure_is_retried(send_mock, no_backoff_sleep):
    send_mock.side_effect = [ConnectionError("reset"), TimeoutError("slow"), None]

    await build_sender().send("user@example.org", "Verify your email", "ABC234")

    assert send_mock.await_count == 3


async def test_gives_up_after_three_attempts_and_raises(send_mock, no_backoff_sleep):
    send_mock.side_effect = ConnectionError("down")

    with pytest.raises(ConnectionError):
        await build_sender().send("user@example.org", "Verify your email", "ABC234")

    assert send_mock.await_count == 3


async def test_a_rejected_login_is_not_retried(send_mock, no_backoff_sleep):
    send_mock.side_effect = smtp_email_sender.aiosmtplib.SMTPAuthenticationError(535, "bad credentials")

    with pytest.raises(smtp_email_sender.aiosmtplib.SMTPAuthenticationError):
        await build_sender().send("user@example.org", "Verify your email", "ABC234")

    assert send_mock.await_count == 1
