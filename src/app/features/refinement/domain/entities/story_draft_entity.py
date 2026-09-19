"""Story draft entity - domain model for AI-generated story drafts awaiting approval."""

from datetime import datetime

from dateutil.tz import UTC

from src.app.features.refinement.domain.validators.refinement_validators import RefinementValidators
from src.app.features.refinement.domain.value_objects.draft_status import DraftStatus
from src.app.shared.domain.entities.base_entity import BaseEntity
from src.app.shared.domain.value_objects.entity_id import EntityId


class StoryDraftEntity(BaseEntity):
    """
    Story draft entity representing an AI-generated user story pending approval.

    Drafts have a simple lifecycle: DRAFT → APPLIED.
    AI generates the final content in one pass — there is no separate refinement step.
    """

    def __init__(
        self,
        id: EntityId,
        title: str,
        description: str | None,
        acceptance_criteria: list[str],
        project_id: EntityId,
        created_by: EntityId,
        status: DraftStatus,
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
    ):
        """
        Initialize StoryDraftEntity.

        Args:
            id: Unique draft identifier
            title: AI-generated story title
            description: AI-generated story description
            acceptance_criteria: AI-generated acceptance criteria
            project_id: Associated project ID
            created_by: User ID of creator
            status: Current draft status (DRAFT or APPLIED)
            created_at: Creation timestamp
            updated_at: Last update timestamp
        """
        RefinementValidators.validate_title(title)

        now = datetime.now(UTC)
        super().__init__(
            id=id,
            created_at=created_at or now,
            updated_at=updated_at or now,
        )

        self._title = title
        self._description = description
        self._acceptance_criteria = acceptance_criteria or []
        self._project_id = project_id
        self._created_by = created_by
        self._status = status

    @property
    def title(self) -> str:
        """Get story title."""
        return self._title

    @property
    def description(self) -> str | None:
        """Get story description."""
        return self._description

    @property
    def acceptance_criteria(self) -> list[str]:
        """Get acceptance criteria."""
        return self._acceptance_criteria

    @property
    def project_id(self) -> EntityId:
        """Get associated project ID."""
        return self._project_id

    @property
    def created_by(self) -> EntityId:
        """Get creator user ID."""
        return self._created_by

    @property
    def status(self) -> DraftStatus:
        """Get draft status."""
        return self._status

    def mark_applied(self) -> None:
        """Mark the draft as applied (converted to a real story)."""
        self._status = DraftStatus.APPLIED
        self.mark_as_updated()

    def update_draft(
        self,
        title: str | None = None,
        description: str | None = None,
        acceptance_criteria: list[str] | None = None,
    ) -> None:
        """
        Update draft fields. Only modifies fields that are explicitly provided.

        Args:
            title: New title (validated if provided)
            description: New description
            acceptance_criteria: New acceptance criteria
        """
        if title is not None:
            RefinementValidators.validate_title(title)
            self._title = title

        if description is not None:
            self._description = description

        if acceptance_criteria is not None:
            self._acceptance_criteria = acceptance_criteria

        self.mark_as_updated()

    @classmethod
    def create(
        cls,
        title: str,
        project_id: EntityId,
        created_by: EntityId,
        description: str | None = None,
        acceptance_criteria: list[str] | None = None,
    ) -> "StoryDraftEntity":
        """
        Factory method to create a new story draft.

        Args:
            title: Story title
            project_id: Associated project ID
            created_by: User ID of creator
            description: Optional description
            acceptance_criteria: Optional acceptance criteria

        Returns:
            New StoryDraftEntity instance
        """
        return cls(
            id=EntityId.generate(),
            title=title,
            description=description,
            acceptance_criteria=acceptance_criteria or [],
            project_id=project_id,
            created_by=created_by,
            status=DraftStatus.default(),
        )
