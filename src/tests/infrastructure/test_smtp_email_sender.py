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
