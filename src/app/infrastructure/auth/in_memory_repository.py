from collections.abc import Sequence

from src.app.domain.auth.entities import User


class InMemoryUserRepository:
    def __init__(self, users: Sequence[User] | None = None) -> None:
        seed_users = list(users) if users is not None else _default_users()
        self._users_by_email = {user.email.lower(): user for user in seed_users}

    def get_by_email(self, email: str) -> User | None:
        return self._users_by_email.get(email.strip().lower())


def _default_users() -> list[User]:
    return [
        User(
            id="user-1",
            email="alonsonh94@gmail.com",
            password="demo123!A",
            display_name="Alonso",
        )
    ]
