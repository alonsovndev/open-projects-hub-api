"""Tests for AI credits on the user aggregate (FR-010-01, FR-010-02)."""

import pytest

from src.app.features.user.domain.entities.user_entity import INITIAL_AI_CREDITS, UserEntity
from src.app.features.user.domain.exceptions.user_exceptions import AICreditsExhaustedError
from src.app.features.user.domain.value_objects.user_role import UserRole


def build_user(role: UserRole = UserRole.ADMIN) -> UserEntity:
    return UserEntity.create(
        email="admin@example.com",
        display_name="Admin",
        password_hash="hashed",
        role=role,
    )


class TestInitialGrant:
    """FR-010-01: a new account starts with five free refinements."""

    def test_a_new_account_is_granted_five_credits(self):
        user = build_user()
        assert user.ai_credits_remaining == 5
        assert user.ai_credits_granted == 5

    def test_the_grant_constant_is_five(self):
        assert INITIAL_AI_CREDITS == 5

    def test_the_granted_total_is_recorded_separately_from_the_remainder(self):
        """The UI renders "3 of 5", so the original grant must survive being spent."""
        user = build_user()
        user.consume_ai_credit()
        user.consume_ai_credit()

        assert user.ai_credits_remaining == 3
        assert user.ai_credits_granted == 5


class TestCreditConsumption:
    """FR-010-02: one credit per successful refinement, and no going below zero."""

    def test_consuming_decrements_by_exactly_one(self):
        user = build_user()
        user.consume_ai_credit()
        assert user.ai_credits_remaining == 4

    def test_has_credits_reports_availability(self):
        user = build_user()
        assert user.has_ai_credits() is True

        for _ in range(INITIAL_AI_CREDITS):
            user.consume_ai_credit()

        assert user.has_ai_credits() is False

    def test_consuming_a_credit_marks_the_record_updated(self):
        user = build_user()
        before = user.updated_at
        user.consume_ai_credit()
        assert user.updated_at >= before

    def test_cannot_go_below_zero(self):
        user = build_user()
        for _ in range(INITIAL_AI_CREDITS):
            user.consume_ai_credit()

        with pytest.raises(AICreditsExhaustedError):
            user.consume_ai_credit()

        assert user.ai_credits_remaining == 0

    def test_the_exhaustion_message_points_at_adding_a_key(self):
        user = build_user()
        for _ in range(INITIAL_AI_CREDITS):
            user.consume_ai_credit()

        with pytest.raises(AICreditsExhaustedError, match="Add your own API key"):
            user.consume_ai_credit()
