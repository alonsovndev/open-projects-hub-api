"""Shared validation logic for project domain."""

from datetime import date

from src.app.shared.domain.exceptions.domain_exceptions import ValidationError


class ProjectValidators:
    """Centralized validation rules for project entities and DTOs."""

    # Validation constants
    MAX_NAME_LENGTH = 255
    MAX_CODE_LENGTH = 50

    @staticmethod
    def validate_name(name: str) -> None:
        """
        Validate project name.

        Args:
            name: Project name to validate

        Raises:
            ValidationError: If name is invalid
        """
        if not name or not name.strip():
            raise ValidationError("Project name cannot be empty")
        if len(name) > ProjectValidators.MAX_NAME_LENGTH:
            raise ValidationError(f"Project name cannot exceed {ProjectValidators.MAX_NAME_LENGTH} characters")

    @staticmethod
    def validate_code(code: str) -> None:
        """
        Validate project code.

        Args:
            code: Project code to validate

        Raises:
            ValidationError: If code is invalid
        """
        if not code or not code.strip():
            raise ValidationError("Project code cannot be empty")
        if len(code) > ProjectValidators.MAX_CODE_LENGTH:
            raise ValidationError(f"Project code cannot exceed {ProjectValidators.MAX_CODE_LENGTH} characters")

    @staticmethod
    def validate_dates(start_date: date | None, end_date: date | None) -> None:
        """
        Validate start and end dates to prevent logical inconsistencies.

        Args:
            start_date: Optional project start date
            end_date: Optional project end date

        Raises:
            ValidationError: If end_date is before start_date
        """
        if start_date and end_date and end_date < start_date:
            raise ValidationError("End date cannot be before start date")
