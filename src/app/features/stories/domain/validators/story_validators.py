"""Shared validation logic for story domain."""

from src.app.shared.domain.exceptions.domain_exceptions import ValidationError


class StoryValidators:
    """Centralized validation rules for story entities and DTOs."""

    # Validation constants
    MAX_TITLE_LENGTH = 255
    MIN_POINTS = 0
    MAX_POINTS = 100
    MAX_ACCEPTANCE_CRITERION_LENGTH = 500

    @staticmethod
    def validate_title(title: str) -> None:
        """
        Validate story title.

        Args:
            title: Story title to validate

        Raises:
            ValidationError: If title is invalid
        """
        if not title or not title.strip():
            raise ValidationError("Story title cannot be empty")
        if len(title) > StoryValidators.MAX_TITLE_LENGTH:
            raise ValidationError(f"Story title cannot exceed {StoryValidators.MAX_TITLE_LENGTH} characters")

    @staticmethod
    def validate_points(points: int | None) -> None:
        """
        Validate story points to ensure reasonable estimation bounds.

        Args:
            points: Story points to validate

        Raises:
            ValidationError: If points are invalid
        """
        if points is not None and points < StoryValidators.MIN_POINTS:
            raise ValidationError("Story points cannot be negative")
        if points is not None and points > StoryValidators.MAX_POINTS:
            raise ValidationError(f"Story points cannot exceed {StoryValidators.MAX_POINTS}")

    @staticmethod
    def validate_acceptance_criteria(acceptance_criteria: list[str]) -> None:
        """
        Validate a story's acceptance criteria.

        An empty list is allowed — a story created by hand may have none yet. A blank
        criterion is not, because it renders as an empty bullet in the Markdown export.

        Args:
            acceptance_criteria: Criteria to validate

        Raises:
            ValidationError: If any criterion is blank or too long
        """
        for criterion in acceptance_criteria:
            if not criterion or not criterion.strip():
                raise ValidationError("Acceptance criteria cannot contain empty entries")
            if len(criterion) > StoryValidators.MAX_ACCEPTANCE_CRITERION_LENGTH:
                raise ValidationError(
                    f"An acceptance criterion cannot exceed "
                    f"{StoryValidators.MAX_ACCEPTANCE_CRITERION_LENGTH} characters"
                )
