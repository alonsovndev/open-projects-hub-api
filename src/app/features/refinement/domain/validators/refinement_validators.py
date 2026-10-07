"""Refinement domain validators."""

from src.app.shared.domain.exceptions.domain_exceptions import ValidationError


class RefinementValidators:
    """Centralized validation rules for refinement entities and DTOs."""

    # Validation constants
    MIN_TITLE_LENGTH = 1
    MAX_TITLE_LENGTH = 500
    MIN_NOTES_LENGTH = 20
    MAX_NOTES_LENGTH = 5000

    @staticmethod
    def validate_title(title: str) -> None:
        """
        Validate story title.

        Args:
            title: Title to validate

        Raises:
            ValidationError: If title is invalid
        """
        if not title or not title.strip():
            raise ValidationError("Story title cannot be empty")

        if len(title) > RefinementValidators.MAX_TITLE_LENGTH:
            raise ValidationError(f"Story title cannot exceed {RefinementValidators.MAX_TITLE_LENGTH} characters")

    @staticmethod
    def validate_raw_notes(raw_notes: str) -> None:
        """
        Validate raw discovery notes.

        Args:
            raw_notes: Notes to validate

        Raises:
            ValidationError: If notes are invalid
        """
        if not raw_notes or not raw_notes.strip():
            raise ValidationError("Raw notes cannot be empty")

        if len(raw_notes) < RefinementValidators.MIN_NOTES_LENGTH:
            raise ValidationError(f"Raw notes must be at least {RefinementValidators.MIN_NOTES_LENGTH} characters")

        if len(raw_notes) > RefinementValidators.MAX_NOTES_LENGTH:
            raise ValidationError(
                f"Raw notes cannot exceed {RefinementValidators.MAX_NOTES_LENGTH} characters "
                f"(received {len(raw_notes)}). Shorten the notes and try again."
            )

    @staticmethod
    def validate_project_id(project_id: str) -> None:
        """
        Validate project ID.

        Args:
            project_id: Project ID to validate

        Raises:
            ValidationError: If project ID is invalid
        """
        if not project_id or not project_id.strip():
            raise ValidationError("Project ID is required")
