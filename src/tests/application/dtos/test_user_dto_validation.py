"""
Tests for UserCreateRequest password validation.

Tests the password complexity requirements.
"""

import pytest
from pydantic import ValidationError

from src.app.features.user.application.dtos.user_dto import UserCreateRequest


class TestPasswordComplexityValidation:
    """Test password complexity validation rules."""

    def test_valid_password_passes_validation(self):
        """Test that a valid password passes all validation rules."""
        user_request = UserCreateRequest(display_name="John Doe", email="john@example.com", password="SecurePass123")

        assert user_request.password == "SecurePass123"

    def test_password_too_short_raises_error(self):
        """Test that password shorter than 8 characters is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            UserCreateRequest(
                display_name="John Doe",
                email="john@example.com",
                password="Short1",  # Only 6 characters
            )

        errors = exc_info.value.errors()
        assert any("at least 8 characters" in str(error["msg"]) for error in errors)

    def test_password_missing_letter_raises_error(self):
        """Test that password without letter is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            UserCreateRequest(
                display_name="John Doe",
                email="john@example.com",
                password="12345678",  # No letters
            )

        errors = exc_info.value.errors()
        assert any("letter" in str(error["msg"]) for error in errors)

    def test_password_missing_digit_raises_error(self):
        """Test that password without digit is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            UserCreateRequest(
                display_name="John Doe",
                email="john@example.com",
                password="NoDigitsHere",  # No digit
            )

        errors = exc_info.value.errors()
        assert any("digit" in str(error["msg"]) for error in errors)

    def test_password_with_special_characters_is_allowed(self):
        """Test that passwords with special characters are accepted."""
        user_request = UserCreateRequest(display_name="John Doe", email="john@example.com", password="Secure@Pass123!")

        assert user_request.password == "Secure@Pass123!"

    def test_exactly_8_characters_with_all_requirements_passes(self):
        """Test that exactly 8 characters with all requirements passes."""
        user_request = UserCreateRequest(
            display_name="John Doe",
            email="john@example.com",
            password="Pass123x",  # Exactly 8 chars
        )

        assert user_request.password == "Pass123x"
