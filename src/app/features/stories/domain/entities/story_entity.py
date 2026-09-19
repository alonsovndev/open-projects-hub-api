"""Story entity - domain model for user stories."""

from datetime import UTC, datetime

from src.app.features.stories.domain.validators.story_validators import StoryValidators
from src.app.features.stories.domain.value_objects.story_priority import StoryPriority
from src.app.features.stories.domain.value_objects.story_status import StoryStatus
from src.app.shared.domain.entities.base_entity import BaseEntity
from src.app.shared.domain.value_objects.entity_id import EntityId


class StoryEntity(BaseEntity):
    """
    Story entity representing a user story in a project.

    Stories are tasks or features within a project with a lifecycle
    from todo to in_progress to done.
    """

    def __init__(
        self,
        id: EntityId,
        title: str,
        description: str | None,
        project_id: EntityId,
        created_by: EntityId,
        assigned_to: EntityId | None,
        status: StoryStatus,
        priority: StoryPriority,
        points: int | None,
        created_at: datetime,
        updated_at: datetime,
    ):
        """
        Initialize StoryEntity.

        Args:
            id: Unique story identifier
            title: Story title (required, max 255 chars)
            description: Optional story description
            project_id: ID of parent project
            created_by: User ID of story creator
            assigned_to: User ID of assigned developer (optional)
            status: Story status (todo, in_progress, done)
            priority: Story priority (low, medium, high)
            points: Story points (optional, for agile estimation)
            created_at: Timestamp when story was created
            updated_at: Timestamp when story was last updated

        Raises:
            ValueError: If validation fails
        """
        StoryValidators.validate_title(title)
        StoryValidators.validate_points(points)

        super().__init__(id=id, created_at=created_at, updated_at=updated_at)

        self._title = title
        self._description = description
        self._project_id = project_id
        self._created_by = created_by
        self._assigned_to = assigned_to
        self._status = status
        self._priority = priority
        self._points = points

    @property
    def title(self) -> str:
        """Get story title."""
        return self._title

    @property
    def description(self) -> str | None:
        """Get story description."""
        return self._description

    @property
    def project_id(self) -> EntityId:
        """Get parent project ID."""
        return self._project_id

    @property
    def created_by(self) -> EntityId:
        """Get creator user ID."""
        return self._created_by

    @property
    def assigned_to(self) -> EntityId | None:
        """Get assigned user ID."""
        return self._assigned_to

    @property
    def status(self) -> StoryStatus:
        """Get story status."""
        return self._status

    @property
    def priority(self) -> StoryPriority:
        """Get story priority."""
        return self._priority

    @property
    def points(self) -> int | None:
        """Get story points."""
        return self._points

    def update_details(
        self,
        title: str | None = None,
        description: str | None = None,
        status: StoryStatus | None = None,
        priority: StoryPriority | None = None,
        points: int | None = None,
    ) -> None:
        """
        Update story details.

        Args:
            title: New title (if provided)
            description: New description (if provided)
            status: New status (if provided)
            priority: New priority (if provided)
            points: New points (if provided)

        Raises:
            ValueError: If validation fails
        """
        if title is not None:
            StoryValidators.validate_title(title)
            self._title = title

        if description is not None:
            self._description = description

        if status is not None:
            self._status = status

        if priority is not None:
            self._priority = priority

        if points is not None:
            StoryValidators.validate_points(points)
            self._points = points

        self.mark_as_updated()

    def assign_to(self, user_id: EntityId) -> None:
        """Assign story to a user."""
        self._assigned_to = user_id
        self.mark_as_updated()

    def unassign(self) -> None:
        """Unassign story from current user."""
        self._assigned_to = None
        self.mark_as_updated()

    def start(self) -> None:
        """Mark story as in progress."""
        self._status = StoryStatus.IN_PROGRESS
        self.mark_as_updated()

    def complete(self) -> None:
        """Mark story as done."""
        self._status = StoryStatus.DONE
        self.mark_as_updated()

    def reopen(self) -> None:
        """Reopen a completed story."""
        self._status = StoryStatus.TODO
        self.mark_as_updated()

    @classmethod
    def create(
        cls,
        title: str,
        project_id: EntityId,
        created_by: EntityId,
        description: str | None = None,
        assigned_to: EntityId | None = None,
        priority: StoryPriority | None = None,
        points: int | None = None,
    ) -> "StoryEntity":
        """
        Factory method to create a new story.

        Args:
            title: Story title
            project_id: Parent project ID
            created_by: User ID of creator
            description: Optional description
            assigned_to: Optional assigned user ID
            priority: Optional priority (defaults to medium)
            points: Optional story points

        Returns:
            New StoryEntity instance

        Raises:
            ValueError: If validation fails
        """
        now = datetime.now(tz=UTC)
        return cls(
            id=EntityId.generate(),
            title=title,
            description=description,
            project_id=project_id,
            created_by=created_by,
            assigned_to=assigned_to,
            status=StoryStatus.default(),
            priority=priority or StoryPriority.default(),
            points=points,
            created_at=now,
            updated_at=now,
        )
