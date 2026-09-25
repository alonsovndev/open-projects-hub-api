"""Tests for the per-user API key validation budget (NFR-010-03)."""

import pytest
from freezegun import freeze_time

from src.app.features.ai_config.domain.exceptions.ai_config_exceptions import KeyValidationRateLimitedError
from src.app.features.ai_config.domain.services.key_validation_throttle import KeyValidationThrottle
from src.app.features.ai_config.infrastructure.repositories.in_memory_key_validation_attempt_repository import (
    InMemoryKeyValidationAttemptRepository,
)


USER_ID = "8f14e45f-ceea-467a-9f84-9e0b1c2d3e4f"
OTHER_USER_ID = "1a2b3c4d-5e6f-4a7b-8c9d-0e1f2a3b4c5d"


def build_throttle() -> KeyValidationThrottle:
    return KeyValidationThrottle(InMemoryKeyValidationAttemptRepository())


class TestKeyValidationThrottle:
    """Five attempts per user per hour, counted in a fixed window."""

    @pytest.mark.asyncio
    async def test_allows_the_first_five_attempts(self):
        throttle = build_throttle()
        for _ in range(KeyValidationThrottle.MAX_ATTEMPTS):
            await throttle.consume(USER_ID)

    @pytest.mark.asyncio
    async def test_rejects_the_sixth_attempt(self):
        throttle = build_throttle()
        for _ in range(KeyValidationThrottle.MAX_ATTEMPTS):
            await throttle.consume(USER_ID)

        with pytest.raises(KeyValidationRateLimitedError) as exc_info:
            await throttle.consume(USER_ID)

        assert exc_info.value.retry_after_seconds > 0

    @pytest.mark.asyncio
    async def test_the_budget_is_per_user(self):
        """One user exhausting their budget must not lock anyone else out."""
        throttle = build_throttle()
        for _ in range(KeyValidationThrottle.MAX_ATTEMPTS):
            await throttle.consume(USER_ID)

        await throttle.consume(OTHER_USER_ID)

    @pytest.mark.asyncio
    async def test_the_window_reopens_after_an_hour(self):
        throttle = build_throttle()

        with freeze_time("2026-09-20 10:00:00"):
            for _ in range(KeyValidationThrottle.MAX_ATTEMPTS):
                await throttle.consume(USER_ID)
            with pytest.raises(KeyValidationRateLimitedError):
                await throttle.consume(USER_ID)

        with freeze_time("2026-09-20 11:00:01"):
            await throttle.consume(USER_ID)

    @pytest.mark.asyncio
    async def test_the_window_stays_closed_inside_the_hour(self):
        throttle = build_throttle()

        with freeze_time("2026-09-20 10:00:00"):
            for _ in range(KeyValidationThrottle.MAX_ATTEMPTS):
                await throttle.consume(USER_ID)

        with freeze_time("2026-09-20 10:59:00"):
            with pytest.raises(KeyValidationRateLimitedError) as exc_info:
                await throttle.consume(USER_ID)
            assert exc_info.value.retry_after_seconds == pytest.approx(60, abs=2)

    @pytest.mark.asyncio
    async def test_reset_clears_the_budget(self):
        throttle = build_throttle()
        for _ in range(KeyValidationThrottle.MAX_ATTEMPTS):
            await throttle.consume(USER_ID)

        await throttle.reset(USER_ID)

        await throttle.consume(USER_ID)

    @pytest.mark.asyncio
    async def test_the_limit_message_tells_the_user_when_to_retry(self):
        throttle = build_throttle()
        for _ in range(KeyValidationThrottle.MAX_ATTEMPTS):
            await throttle.consume(USER_ID)

        with pytest.raises(KeyValidationRateLimitedError, match="Validation limit reached"):
            await throttle.consume(USER_ID)
