"""Shared validation logic for user domain."""

import re


class UserValidators:
    """Centralized validation rules for user entities and DTOs."""

    # Validation constants
    MIN_PASSWORD_LENGTH = 8
    MIN_DISPLAY_NAME_LENGTH = 1
    MAX_DISPLAY_NAME_LENGTH = 255

    @staticmethod
    def validate_password(password: str) -> None:
        """
        Validate password meets complexity requirements:
        - At least 8 characters
        - At least one letter
        - At least one digit

        Args:
            password: Password string to validate

        Raises:
            ValueError: If password doesn't meet requirements
        """
        if len(password) < UserValidators.MIN_PASSWORD_LENGTH:
            raise ValueError(f"Password must be at least {UserValidators.MIN_PASSWORD_LENGTH} characters long")

        if not re.search(r"[a-zA-Z]", password):
            raise ValueError("Password must contain at least one letter")

        if not re.search(r"\d", password):
            raise ValueError("Password must contain at least one digit")

    @staticmethod
    def validate_display_name(display_name: str) -> None:
        """
        Validate display name.

        Args:
            display_name: Display name to validate

        Raises:
            ValueError: If display name is invalid
        """
        if not display_name or not display_name.strip():
            raise ValueError("Display name cannot be empty")

        if len(display_name) > UserValidators.MAX_DISPLAY_NAME_LENGTH:
            raise ValueError(f"Display name cannot exceed {UserValidators.MAX_DISPLAY_NAME_LENGTH} characters")
