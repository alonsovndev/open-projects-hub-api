"""Tests for first-use onboarding state on the user aggregate (F-005)."""

from datetime import UTC, datetime

from src.app.features.user.domain.entities.user_entity import UserEntity
from src.app.features.user.domain.value_objects.user_role import UserRole


def build_user() -> UserEntity:
    return UserEntity.create(
        email="admin@example.com",
        display_name="Admin",
        password_hash="hashed",
        role=UserRole.ADMIN,
    )


class TestOnboarding:
    def test_a_new_account_has_not_completed_onboarding(self):
        user = build_user()

        assert user.onboarding_completed_at is None
        assert user.is_onboarding_completed is False

    def test_completing_records_the_time(self):
        user = build_user()
        completed_at = datetime(2026, 10, 26, 12, 0, tzinfo=UTC)

        user.complete_onboarding(now=completed_at)

        assert user.is_onboarding_completed is True
        assert user.onboarding_completed_at == completed_at

    def test_completing_twice_keeps_the_first_time(self):
        user = build_user()
        first = datetime(2026, 10, 26, 12, 0, tzinfo=UTC)

        user.complete_onboarding(now=first)
        user.complete_onboarding(now=datetime(2026, 10, 27, 12, 0, tzinfo=UTC))

        assert user.onboarding_completed_at == first

    def test_reset_shows_onboarding_again(self):
        user = build_user()
        user.complete_onboarding()

        user.reset_onboarding()

        assert user.is_onboarding_completed is False
        assert user.onboarding_completed_at is None
