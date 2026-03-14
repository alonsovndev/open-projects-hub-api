from typing import Protocol

from src.app.domain.auth.entities import User


class UserRepository(Protocol):
    def get_by_email(self, email: str) -> User | None:
        """Return a user by email when it exists."""
