from collections.abc import Callable
from datetime import datetime, timezone

from src.app.application.auth.dto import LoginCommand, LoginResult
from src.app.domain.auth.errors import InvalidCredentialsError
from src.app.domain.auth.repositories import UserRepository


class LoginUseCase:
    def __init__(
        self,
        user_repository: UserRepository,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self._user_repository = user_repository
        self._clock = clock or (lambda: datetime.now(timezone.utc))

    def execute(self, command: LoginCommand) -> LoginResult:
        normalized_email = command.email.strip().lower()
        user = self._user_repository.get_by_email(normalized_email)

        if user is None or user.password != command.password:
            raise InvalidCredentialsError("Invalid credentials")

        return LoginResult(
            token=f"mock-token-{user.id}",
            email=user.email,
            display_name=user.display_name,
            logged_in_at=_format_datetime(self._clock()),
        )


def _format_datetime(value: datetime) -> str:
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)

    utc_value = value.astimezone(timezone.utc).replace(microsecond=0)
    return utc_value.isoformat().replace("+00:00", "Z")
