"""
Minimal SMTP email sender.

Delivers password-reset codes (EPIC-2) and sign-up verification codes
(EPIC-8) as plain text. Transient connection failures are retried with
exponential backoff (EPIC-9-BE-001); the per-account hourly cap lives with the
code issuers, which know the account.
"""

from email.message import EmailMessage
from email.utils import formatdate

import aiosmtplib

from src.app.shared.infrastructure.email.email_sender import EmailSender
from src.app.shared.infrastructure.retry import retry_on_exception
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
        message["Date"] = formatdate(localtime=False)
        message.set_content(body)

        try:
            await self._deliver(message)
        except Exception:
            self._log.exception("Failed to send email", extra={"event_type": "email.send_failed", "to": mask_email(to)})
            raise

    # Only connection and timeout errors are retried; a rejected login or recipient will not heal.
    @retry_on_exception(max_tries=3)
    async def _deliver(self, message: EmailMessage) -> None:
        await aiosmtplib.send(
            message,
            hostname=self.host,
            port=self.port,
            username=self.username or None,
            password=self.password or None,
            start_tls=self.use_tls,
        )
