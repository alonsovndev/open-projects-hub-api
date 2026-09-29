"""
Minimal SMTP email sender.

Delivers password-reset codes (EPIC-2) and sign-up verification codes
(EPIC-8) as plain text. EPIC-9-BE-001 (Email Notification Service) will add
retry/backoff and per-account rate limiting; this adapter intentionally stays
small until that lands.
"""

from email.message import EmailMessage

import aiosmtplib

from src.app.shared.infrastructure.email.email_sender import EmailSender
from src.app.shared.logging import get_logger, mask_email


class SmtpEmailSender(EmailSender):
    def __init__(self, host: str, port: int, username: str, password: str, from_address: str, use_tls: bool = True):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.from_address = from_address
        self.use_tls = use_tls
        self._log = get_logger(__name__)

    async def send(self, to: str, subject: str, body: str) -> None:
        message = EmailMessage()
        message["From"] = self.from_address
        message["To"] = to
        message["Subject"] = subject
        message.set_content(body)

        try:
            await aiosmtplib.send(
                message,
                hostname=self.host,
                port=self.port,
                username=self.username or None,
                password=self.password or None,
                start_tls=self.use_tls,
            )
        except Exception:
            self._log.exception("Failed to send email", extra={"event_type": "email.send_failed", "to": mask_email(to)})
            raise
