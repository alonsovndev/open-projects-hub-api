"""
Tests for UserCreateRequest.

Invited members choose their own password when they verify their email, so the request
carries no password.
"""

import pytest
from pydantic import ValidationError

from src.app.features.user.application.dtos.user_dto import UserCreateRequest


class TestUserCreateRequest:
    def test_accepts_name_email_and_role_without_a_password(self):
        user_request = UserCreateRequest(display_name="John Doe", email="john@example.com", role="member")

        assert user_request.role == "member"
        assert not hasattr(user_request, "password")

    def test_a_supplied_password_is_ignored(self):
        user_request = UserCreateRequest.model_validate(
            {"displayName": "John Doe", "email": "john@example.com", "password": "SecurePass123"}
        )

        assert not hasattr(user_request, "password")

    @pytest.mark.parametrize("role", ["viewer", "admin"])
    def test_only_the_member_role_can_be_assigned(self, role):
        with pytest.raises(ValidationError):
            UserCreateRequest(display_name="John Doe", email="john@example.com", role=role)
