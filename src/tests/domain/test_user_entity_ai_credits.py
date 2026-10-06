"""Tests for AI credits on the user aggregate (FR-010-01, FR-010-02)."""

import pytest

from src.app.features.user.domain.entities.user_entity import INITIAL_AI_CREDITS, UserEntity
from src.app.features.user.domain.exceptions.user_exceptions import AICreditsExhaustedError
from src.app.features.user.domain.value_objects.user_role import UserRole
from src.app.shared.domain.value_objects.entity_id import EntityId


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


class TestCreditsAwaitEmailVerification:
    """FR-010-01: a self-registered account earns its free credits by verifying its email."""

    def build_pending_user(self) -> UserEntity:
        return UserEntity.create_pending_verification(
            email="new@example.com",
            display_name="New User",
            password_hash="hashed",
            role=UserRole.ADMIN,
        )

    def test_a_pending_account_starts_without_credits(self):
        user = self.build_pending_user()

        assert user.is_email_verified is False
        assert user.ai_credits_remaining == 0
        assert user.ai_credits_granted == 0

    def test_verifying_the_email_sets_the_granted_credits(self):
        user = self.build_pending_user()

        user.verify_email(granted_credits=INITIAL_AI_CREDITS)

        assert user.is_email_verified is True
        assert user.ai_credits_remaining == INITIAL_AI_CREDITS
        assert user.ai_credits_granted == INITIAL_AI_CREDITS

    def test_verifying_without_a_grant_leaves_no_credits(self):
        """The caller reserves credits from the workspace ceiling; none reserved means none granted."""
        user = UserEntity.create_workspace_member(
            email="mate@example.com",
            display_name="Mate",
            password_hash="hash",
            role=UserRole.MEMBER,
            workspace_id=EntityId.generate(),
        )

        user.verify_email()

        assert user.is_email_verified is True
        assert user.ai_credits_remaining == 0
        assert user.ai_credits_granted == 0

    def test_accounts_created_by_an_admin_are_verified_on_creation(self):
        assert build_user().is_email_verified is True
