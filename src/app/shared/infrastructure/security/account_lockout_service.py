"""
Account lockout service for preventing brute-force attacks.

Implements progressive account lockout after consecutive failed login attempts.
Uses in-memory storage with Redis-ready design for horizontal scaling.
"""

import asyncio
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta


@dataclass
class LockoutState:
    """Represents the lockout state for a user account."""

    failed_attempts: int
    locked_until: datetime | None
    last_attempt: datetime


class AccountLockoutService:
    """
    Manages account lockout for failed login attempts.

    Configuration:
    - MAX_FAILED_ATTEMPTS: Number of failures before lockout (default: 5)
    - LOCKOUT_DURATION_MINUTES: Base lockout duration (default: 15)
    - PROGRESSIVE_LOCKOUT: Use exponential backoff (default: True)
    - ATTEMPT_WINDOW_MINUTES: Time window for counting attempts (default: 30)

    Lockout progression (if PROGRESSIVE_LOCKOUT=True):
    - 5 failures: 15 minutes
    - 10 failures: 30 minutes
    - 15 failures: 60 minutes
    - 20+ failures: 120 minutes (2 hours)
    """

    # Configuration (can be overridden via environment variables)
    MAX_FAILED_ATTEMPTS = 5
    LOCKOUT_DURATION_MINUTES = 15
    PROGRESSIVE_LOCKOUT = True
    ATTEMPT_WINDOW_MINUTES = 30

    def __init__(self):
        """
        Initialize account lockout service.

        Note: Uses in-memory storage. For production with multiple instances,
        replace with Redis backend.
        """
        self._lockout_state: dict[str, LockoutState] = {}
        self._lock = asyncio.Lock()

    async def record_failed_attempt(self, user_identifier: str) -> None:
        """
        Record a failed login attempt for a user.

        Args:
            user_identifier: Unique identifier (email or user_id)
        """
        async with self._lock:
            now = datetime.now(tz=UTC)

            if user_identifier not in self._lockout_state:
                self._lockout_state[user_identifier] = LockoutState(
                    failed_attempts=1, locked_until=None, last_attempt=now
                )
            else:
                state = self._lockout_state[user_identifier]

                # Reset counter if last attempt was outside the time window
                time_since_last = now - state.last_attempt
                if time_since_last.total_seconds() > (self.ATTEMPT_WINDOW_MINUTES * 60):
                    state.failed_attempts = 1
                    state.locked_until = None
                else:
                    state.failed_attempts += 1

                state.last_attempt = now

                # Apply lockout if threshold reached
                if state.failed_attempts >= self.MAX_FAILED_ATTEMPTS:
                    lockout_duration = self._calculate_lockout_duration(state.failed_attempts)
                    state.locked_until = now + timedelta(minutes=lockout_duration)

    async def record_successful_login(self, user_identifier: str) -> None:
        """
        Clear failed attempts after successful login.

        Args:
            user_identifier: Unique identifier (email or user_id)
        """
        async with self._lock:
            if user_identifier in self._lockout_state:
                del self._lockout_state[user_identifier]

    async def is_locked_out(self, user_identifier: str) -> bool:
        """
        Check if account is currently locked out.

        Args:
            user_identifier: Unique identifier (email or user_id)

        Returns:
            True if account is locked out, False otherwise
        """
        async with self._lock:
            if user_identifier not in self._lockout_state:
                return False

            state = self._lockout_state[user_identifier]

            if state.locked_until is None:
                return False

            now = datetime.now(tz=UTC)

            # Check if lockout has expired
            if now >= state.locked_until:
                # Lockout expired, reset state
                del self._lockout_state[user_identifier]
                return False

            return True

    async def get_lockout_info(self, user_identifier: str) -> dict | None:
        """
        Get detailed lockout information for a user.

        Args:
            user_identifier: Unique identifier (email or user_id)

        Returns:
            Dictionary with lockout details or None if not locked
        """
        async with self._lock:
            if user_identifier not in self._lockout_state:
                return None

            state = self._lockout_state[user_identifier]
            now = datetime.now(tz=UTC)

            # Check if lockout is active
            if state.locked_until and now < state.locked_until:
                remaining_seconds = int((state.locked_until - now).total_seconds())
                return {
                    "locked": True,
                    "failed_attempts": state.failed_attempts,
                    "locked_until": state.locked_until.isoformat(),
                    "remaining_seconds": remaining_seconds,
                    "remaining_minutes": round(remaining_seconds / 60, 1),
                }

            # Lockout expired or not locked
            if state.locked_until and now >= state.locked_until:
                del self._lockout_state[user_identifier]
                return None

            # Not locked but has failed attempts
            return {
                "locked": False,
                "failed_attempts": state.failed_attempts,
                "remaining_attempts": self.MAX_FAILED_ATTEMPTS - state.failed_attempts,
            }

    async def get_failed_attempts(self, user_identifier: str) -> int:
        """
        Get number of failed attempts for a user.

        Args:
            user_identifier: Unique identifier (email or user_id)

        Returns:
            Number of failed attempts in current window
        """
        async with self._lock:
            if user_identifier not in self._lockout_state:
                return 0

            state = self._lockout_state[user_identifier]
            now = datetime.now(tz=UTC)

            # Check if attempts are within the time window
            time_since_last = now - state.last_attempt
            if time_since_last.total_seconds() > (self.ATTEMPT_WINDOW_MINUTES * 60):
                # Outside window, reset
                del self._lockout_state[user_identifier]
                return 0

            return state.failed_attempts

    def _calculate_lockout_duration(self, failed_attempts: int) -> int:
        """
        Calculate lockout duration based on number of failed attempts.

        Args:
            failed_attempts: Number of consecutive failed attempts

        Returns:
            Lockout duration in minutes
        """
        if not self.PROGRESSIVE_LOCKOUT:
            return self.LOCKOUT_DURATION_MINUTES

        # Progressive lockout with exponential backoff
        if failed_attempts >= 20:
            return 120  # 2 hours
        if failed_attempts >= 15:
            return 60  # 1 hour
        if failed_attempts >= 10:
            return 30  # 30 minutes
        return 15  # 15 minutes (base)

    async def clear_lockout(self, user_identifier: str) -> bool:
        """
        Manually clear lockout state (admin override).

        Args:
            user_identifier: Unique identifier (email or user_id)

        Returns:
            True if lockout was cleared, False if no lockout existed
        """
        async with self._lock:
            if user_identifier in self._lockout_state:
                del self._lockout_state[user_identifier]
                return True
            return False

    async def get_all_locked_accounts(self) -> list[dict]:
        """
        Get list of all currently locked accounts (admin/monitoring).

        Returns:
            List of dictionaries with lockout information
        """
        async with self._lock:
            now = datetime.now(tz=UTC)
            locked_accounts = []

            for identifier, state in list(self._lockout_state.items()):
                if state.locked_until and now < state.locked_until:
                    remaining_seconds = int((state.locked_until - now).total_seconds())
                    locked_accounts.append(
                        {
                            "identifier": identifier,
                            "failed_attempts": state.failed_attempts,
                            "locked_until": state.locked_until.isoformat(),
                            "remaining_seconds": remaining_seconds,
                            "remaining_minutes": round(remaining_seconds / 60, 1),
                        }
                    )
                elif state.locked_until and now >= state.locked_until:
                    # Clean up expired lockouts
                    del self._lockout_state[identifier]

            return locked_accounts


# Singleton instance
_account_lockout_service: AccountLockoutService | None = None


def get_account_lockout_service() -> AccountLockoutService:
    """
    Get singleton instance of AccountLockoutService.

    Returns:
        AccountLockoutService instance
    """
    global _account_lockout_service
    if _account_lockout_service is None:
        _account_lockout_service = AccountLockoutService()
    return _account_lockout_service
