"""
Tests for AccountLockoutService.

Tests account lockout functionality including:
- Failed attempt tracking
- Progressive lockout durations
- Lockout expiration
- Successful login resets
- Time window behavior
"""

import pytest
from freezegun import freeze_time

from src.app.shared.infrastructure.security.account_lockout_service import (
    AccountLockoutService,
    get_account_lockout_service,
)


@pytest.fixture
def lockout_service():
    """Create fresh lockout service instance for each test."""
    service = AccountLockoutService()
    # Reset configuration to defaults
    service.MAX_FAILED_ATTEMPTS = 5
    service.LOCKOUT_DURATION_MINUTES = 15
    service.PROGRESSIVE_LOCKOUT = True
    service.ATTEMPT_WINDOW_MINUTES = 30
    return service


@pytest.fixture
def lockout_service_no_progressive():
    """Create lockout service with progressive lockout disabled."""
    service = AccountLockoutService()
    service.MAX_FAILED_ATTEMPTS = 5
    service.LOCKOUT_DURATION_MINUTES = 15
    service.PROGRESSIVE_LOCKOUT = False
    service.ATTEMPT_WINDOW_MINUTES = 30
    return service


class TestFailedAttemptTracking:
    """Test recording and tracking failed login attempts."""

    @pytest.mark.asyncio
    async def test_first_failed_attempt_recorded(self, lockout_service):
        """Test that first failed attempt is recorded."""
        await lockout_service.record_failed_attempt("user@example.com")

        attempts = await lockout_service.get_failed_attempts("user@example.com")
        assert attempts == 1

    @pytest.mark.asyncio
    async def test_multiple_failed_attempts_increment(self, lockout_service):
        """Test that multiple failed attempts increment counter."""
        user = "user@example.com"

        for _i in range(3):
            await lockout_service.record_failed_attempt(user)

        attempts = await lockout_service.get_failed_attempts(user)
        assert attempts == 3

    @pytest.mark.asyncio
    async def test_no_attempts_returns_zero(self, lockout_service):
        """Test that user with no attempts returns zero."""
        attempts = await lockout_service.get_failed_attempts("newuser@example.com")
        assert attempts == 0

    @pytest.mark.asyncio
    async def test_successful_login_clears_attempts(self, lockout_service):
        """Test that successful login clears failed attempts."""
        user = "user@example.com"

        # Record some failures
        await lockout_service.record_failed_attempt(user)
        await lockout_service.record_failed_attempt(user)
        assert await lockout_service.get_failed_attempts(user) == 2

        # Successful login
        await lockout_service.record_successful_login(user)

        # Attempts should be cleared
        attempts = await lockout_service.get_failed_attempts(user)
        assert attempts == 0


class TestAccountLockout:
    """Test account lockout after threshold reached."""

    @pytest.mark.asyncio
    async def test_account_locked_after_max_attempts(self, lockout_service):
        """Test that account is locked after MAX_FAILED_ATTEMPTS."""
        user = "user@example.com"

        # Not locked before threshold
        assert not await lockout_service.is_locked_out(user)

        # Reach threshold (5 attempts)
        for _i in range(5):
            await lockout_service.record_failed_attempt(user)

        # Should be locked
        assert await lockout_service.is_locked_out(user)

    @pytest.mark.asyncio
    async def test_lockout_before_threshold_not_locked(self, lockout_service):
        """Test that account is not locked below threshold."""
        user = "user@example.com"

        # 4 attempts (below threshold of 5)
        for _i in range(4):
            await lockout_service.record_failed_attempt(user)

        # Should not be locked
        assert not await lockout_service.is_locked_out(user)

    @pytest.mark.asyncio
    async def test_lockout_info_contains_correct_data(self, lockout_service):
        """Test that lockout info contains expected fields."""
        user = "user@example.com"

        # Trigger lockout
        for _i in range(5):
            await lockout_service.record_failed_attempt(user)

        info = await lockout_service.get_lockout_info(user)

        assert info is not None
        assert info["locked"] is True
        assert info["failed_attempts"] == 5
        assert "locked_until" in info
        assert "remaining_seconds" in info
        assert "remaining_minutes" in info
        assert info["remaining_seconds"] > 0

    @pytest.mark.asyncio
    async def test_lockout_info_before_lockout(self, lockout_service):
        """Test lockout info for user with failed attempts but not locked."""
        user = "user@example.com"

        # 3 attempts (not locked)
        for _i in range(3):
            await lockout_service.record_failed_attempt(user)

        info = await lockout_service.get_lockout_info(user)

        assert info is not None
        assert info["locked"] is False
        assert info["failed_attempts"] == 3
        assert info["remaining_attempts"] == 2


class TestLockoutExpiration:
    """Test lockout expiration and time-based behavior."""

    @pytest.mark.asyncio
    async def test_lockout_expires_after_duration(self, lockout_service):
        """Test that lockout expires after lockout duration."""
        user = "user@example.com"

        # Trigger lockout
        with freeze_time("2026-05-11 12:00:00"):
            for _i in range(5):
                await lockout_service.record_failed_attempt(user)
            assert await lockout_service.is_locked_out(user)

        # Advance time by 15 minutes (base lockout duration)
        with freeze_time("2026-05-11 12:15:01"):
            # Should no longer be locked
            assert not await lockout_service.is_locked_out(user)

    @pytest.mark.asyncio
    async def test_lockout_still_active_before_expiration(self, lockout_service):
        """Test that lockout is still active before expiration."""
        user = "user@example.com"

        # Trigger lockout
        with freeze_time("2026-05-11 12:00:00"):
            for _i in range(5):
                await lockout_service.record_failed_attempt(user)
            assert await lockout_service.is_locked_out(user)

        # Advance time by 10 minutes (before 15 min expiration)
        with freeze_time("2026-05-11 12:10:00"):
            # Should still be locked
            assert await lockout_service.is_locked_out(user)

    @pytest.mark.asyncio
    async def test_attempts_reset_after_time_window(self, lockout_service):
        """Test that failed attempts reset after time window expires."""
        user = "user@example.com"

        # Record 2 attempts
        with freeze_time("2026-05-11 12:00:00"):
            await lockout_service.record_failed_attempt(user)
            await lockout_service.record_failed_attempt(user)
            assert await lockout_service.get_failed_attempts(user) == 2

        # Advance past attempt window (30 minutes)
        with freeze_time("2026-05-11 12:31:00"):
            # Attempts should be reset
            assert await lockout_service.get_failed_attempts(user) == 0


class TestProgressiveLockout:
    """Test progressive lockout duration based on attempt count."""

    @pytest.mark.asyncio
    async def test_base_lockout_duration_15_minutes(self, lockout_service):
        """Test base lockout duration is 15 minutes for 5-9 attempts."""
        user = "user@example.com"

        with freeze_time("2026-05-11 12:00:00"):
            # 5 attempts
            for _i in range(5):
                await lockout_service.record_failed_attempt(user)

            info = await lockout_service.get_lockout_info(user)
            # Should be approximately 15 minutes (900 seconds)
            assert 890 <= info["remaining_seconds"] <= 910

    @pytest.mark.asyncio
    async def test_progressive_lockout_30_minutes(self, lockout_service):
        """Test progressive lockout increases to 30 minutes for 10-14 attempts."""
        user = "user@example.com"

        with freeze_time("2026-05-11 12:00:00"):
            # 10 attempts
            for _i in range(10):
                await lockout_service.record_failed_attempt(user)

            info = await lockout_service.get_lockout_info(user)
            # Should be approximately 30 minutes (1800 seconds)
            assert 1790 <= info["remaining_seconds"] <= 1810

    @pytest.mark.asyncio
    async def test_progressive_lockout_60_minutes(self, lockout_service):
        """Test progressive lockout increases to 60 minutes for 15-19 attempts."""
        user = "user@example.com"

        with freeze_time("2026-05-11 12:00:00"):
            # 15 attempts
            for _i in range(15):
                await lockout_service.record_failed_attempt(user)

            info = await lockout_service.get_lockout_info(user)
            # Should be approximately 60 minutes (3600 seconds)
            assert 3590 <= info["remaining_seconds"] <= 3610

    @pytest.mark.asyncio
    async def test_progressive_lockout_120_minutes(self, lockout_service):
        """Test progressive lockout maxes at 120 minutes for 20+ attempts."""
        user = "user@example.com"

        with freeze_time("2026-05-11 12:00:00"):
            # 20 attempts
            for _i in range(20):
                await lockout_service.record_failed_attempt(user)

            info = await lockout_service.get_lockout_info(user)
            # Should be approximately 120 minutes (7200 seconds)
            assert 7190 <= info["remaining_seconds"] <= 7210

    @pytest.mark.asyncio
    async def test_non_progressive_lockout_constant_duration(self, lockout_service_no_progressive):
        """Test that non-progressive lockout uses constant duration."""
        user = "user@example.com"

        with freeze_time("2026-05-11 12:00:00"):
            # 20 attempts (would be 120 min with progressive)
            for _i in range(20):
                await lockout_service_no_progressive.record_failed_attempt(user)

            info = await lockout_service_no_progressive.get_lockout_info(user)
            # Should still be 15 minutes (base duration)
            assert 890 <= info["remaining_seconds"] <= 910


class TestManualLockoutClear:
    """Test manual lockout clearing (admin override)."""

    @pytest.mark.asyncio
    async def test_clear_lockout_removes_lock(self, lockout_service):
        """Test that clearing lockout removes the lock."""
        user = "user@example.com"

        # Trigger lockout
        for _i in range(5):
            await lockout_service.record_failed_attempt(user)
        assert await lockout_service.is_locked_out(user)

        # Clear lockout
        result = await lockout_service.clear_lockout(user)

        assert result is True
        assert not await lockout_service.is_locked_out(user)

    @pytest.mark.asyncio
    async def test_clear_nonexistent_lockout_returns_false(self, lockout_service):
        """Test that clearing non-existent lockout returns False."""
        result = await lockout_service.clear_lockout("nouser@example.com")
        assert result is False


class TestMultipleUsers:
    """Test lockout service with multiple users."""

    @pytest.mark.asyncio
    async def test_lockouts_isolated_per_user(self, lockout_service):
        """Test that lockouts are isolated per user."""
        user1 = "user1@example.com"
        user2 = "user2@example.com"

        # Lock user1
        for _i in range(5):
            await lockout_service.record_failed_attempt(user1)

        # user1 locked, user2 not
        assert await lockout_service.is_locked_out(user1)
        assert not await lockout_service.is_locked_out(user2)

    @pytest.mark.asyncio
    async def test_successful_login_only_clears_specific_user(self, lockout_service):
        """Test that successful login only clears specific user's attempts."""
        user1 = "user1@example.com"
        user2 = "user2@example.com"

        # Record attempts for both
        for _i in range(3):
            await lockout_service.record_failed_attempt(user1)
            await lockout_service.record_failed_attempt(user2)

        # Clear user1
        await lockout_service.record_successful_login(user1)

        # user1 cleared, user2 still has attempts
        assert await lockout_service.get_failed_attempts(user1) == 0
        assert await lockout_service.get_failed_attempts(user2) == 3


class TestGetAllLockedAccounts:
    """Test retrieving all locked accounts."""

    @pytest.mark.asyncio
    async def test_get_all_locked_accounts_returns_locked_only(self, lockout_service):
        """Test that only locked accounts are returned."""
        locked_user = "locked@example.com"
        not_locked_user = "notlocked@example.com"

        # Lock one user
        for _i in range(5):
            await lockout_service.record_failed_attempt(locked_user)

        # Not locked user (only 3 attempts)
        for _i in range(3):
            await lockout_service.record_failed_attempt(not_locked_user)

        locked_accounts = await lockout_service.get_all_locked_accounts()

        assert len(locked_accounts) == 1
        assert locked_accounts[0]["identifier"] == locked_user

    @pytest.mark.asyncio
    async def test_get_all_locked_accounts_empty_when_none(self, lockout_service):
        """Test that empty list returned when no locked accounts."""
        locked_accounts = await lockout_service.get_all_locked_accounts()
        assert locked_accounts == []


class TestSingletonService:
    """Test singleton pattern for lockout service."""

    def test_get_account_lockout_service_returns_singleton(self):
        """Test that get_account_lockout_service returns same instance."""
        service1 = get_account_lockout_service()
        service2 = get_account_lockout_service()

        assert service1 is service2
