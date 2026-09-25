"""Process-local storage for the key validation budget."""

from datetime import UTC, datetime, timedelta

from src.app.features.ai_config.domain.repositories.key_validation_attempt_repository import (
    ChargedAttempt,
    KeyValidationAttemptRepository,
)


class InMemoryKeyValidationAttemptRepository(KeyValidationAttemptRepository):
    """
    Process-local windows. Lost on restart and not shared across instances.

    Default for tests and single-instance runs; production wires the SQL-backed variant so
    the budget cannot be reset by bouncing a container or by landing on another instance.
    """

    def __init__(self) -> None:
        self._windows: dict[str, ChargedAttempt] = {}

    async def charge(self, user_id: str, window_minutes: int) -> ChargedAttempt:
        """
        Record one attempt and return the resulting count.

        Atomic by construction: there is no `await` between the read and the write, and
        asyncio will not interleave another task inside a synchronous block.
        """
        now = datetime.now(tz=UTC)
        current = self._windows.get(user_id)

        if current is None or now >= current.window_started_at + timedelta(minutes=window_minutes):
            charged = ChargedAttempt(attempt_count=1, window_started_at=now)
        else:
            charged = ChargedAttempt(
                attempt_count=current.attempt_count + 1,
                window_started_at=current.window_started_at,
            )

        self._windows[user_id] = charged
        return charged

    async def delete(self, user_id: str) -> None:
        """Drop the user's window, resetting their budget."""
        self._windows.pop(user_id, None)
