"""Storage port for the per-user API key validation budget (NFR-010-03)."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class ChargedAttempt:
    """The user's position in the current window, after an attempt has been recorded."""

    attempt_count: int
    window_started_at: datetime


class KeyValidationAttemptRepository(ABC):
    """Persistence for validation-attempt counters, keyed by user ID."""

    @abstractmethod
    async def charge(self, user_id: str, window_minutes: int) -> ChargedAttempt:
        """
        Record one attempt and return the resulting count, in a single atomic operation.

        Recording and reading must not be separable. A `SELECT` followed by an `UPDATE`
        lets concurrent validation requests all read the same count and each write
        count + 1, so the budget charges once no matter how many calls are in flight —
        which is precisely the unmetered provider probing the limit exists to prevent.

        Implementations are also responsible for rolling the window: if the stored window
        opened more than `window_minutes` ago, the count restarts at 1.

        Args:
            user_id: The user's UUID string.
            window_minutes: How long a window stays open.

        Returns:
            ChargedAttempt with the count including this attempt, and the window's start.
        """

    @abstractmethod
    async def delete(self, user_id: str) -> None:
        """Drop the user's window, resetting their budget."""
