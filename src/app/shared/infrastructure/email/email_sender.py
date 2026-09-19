"""Email sending port. Infrastructure implementations live alongside this file."""

from abc import ABC, abstractmethod


class EmailSender(ABC):
    """Outbound transactional email port."""

    @abstractmethod
    async def send(self, to: str, subject: str, body: str) -> None:
        """Send a plain-text email. Raises on delivery failure."""
