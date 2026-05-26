"""Project entity - domain model for projects."""

from datetime import date, datetime

from src.app.features.projects.domain.validators.project_validators import ProjectValidators
from src.app.features.projects.domain.value_objects.project_priority import ProjectPriority
from src.app.features.projects.domain.value_objects.project_status import ProjectStatus
from src.app.shared.domain.entities.base_entity import BaseEntity
from src.app.shared.domain.value_objects.entity_id import EntityId


class ProjectEntity(BaseEntity):
    """
    Project entity representing a project in the system.

    Projects are containers for user stories and have a lifecycle
    from active to completed/archived.
    """

    def __init__(
        self,
        id: EntityId,
        name: str,
        code: str,
        description: str | None,
        created_by: EntityId,
        client_id: EntityId,
        status: ProjectStatus,
        priority: ProjectPriority,
        start_date: date | None,
        end_date: date | None,
        created_at: datetime,
        updated_at: datetime,
    ):
        """
        Initialize ProjectEntity.

        Args:
            id: Unique project identifier
            name: Project name (required, max 255 chars)
            code: Project code (required, unique, max 50 chars)
            description: Optional project description
            created_by: User ID of project creator
            client_id: Client ID associated with project
            status: Project status (active, completed, archived)
            priority: Project priority (low, medium, high)
            start_date: Optional project start date
            end_date: Optional project end date
            created_at: Timestamp when project was created
            updated_at: Timestamp when project was last updated

        Raises:
            ValueError: If validation fails
        """
        # Validate domain invariants
        ProjectValidators.validate_name(name)
        ProjectValidators.validate_code(code)
        ProjectValidators.validate_dates(start_date, end_date)

        super().__init__(id=id, created_at=created_at, updated_at=updated_at)

        self._name = name
        self._code = code
        self._description = description
        self._created_by = created_by
        self._client_id = client_id
        self._status = status
        self._priority = priority
        self._start_date = start_date
        self._end_date = end_date

    @property
    def name(self) -> str:
        """Get project name."""
        return self._name

    @property
    def code(self) -> str:
        """Get project code."""
        return self._code

    @property
    def description(self) -> str | None:
        """Get project description."""
        return self._description

    @property
    def created_by(self) -> EntityId:
        """Get creator user ID."""
        return self._created_by

    @property
    def client_id(self) -> EntityId:
        """Get client ID."""
        return self._client_id

    @property
    def status(self) -> ProjectStatus:
        """Get project status."""
        return self._status

    @property
    def priority(self) -> ProjectPriority:
        """Get project priority."""
        return self._priority

    @property
    def start_date(self) -> date | None:
        """Get project start date."""
        return self._start_date

    @property
    def end_date(self) -> date | None:
        """Get project end date."""
        return self._end_date

    def update_details(
        self,
        name: str | None = None,
        code: str | None = None,
        description: str | None = None,
        client_id: EntityId | None = None,
        status: ProjectStatus | None = None,
        priority: ProjectPriority | None = None,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> None:
        """
        Update project details.

        Args:
            name: New project name (if provided)
            code: New project code (if provided)
            description: New description (if provided)
            client_id: New client ID (if provided)
            status: New status (if provided)
            priority: New priority (if provided)
            start_date: New start date (if provided)
            end_date: New end date (if provided)

        Raises:
            ValueError: If validation fails
        """
        if name is not None:
            ProjectValidators.validate_name(name)
            self._name = name

        if code is not None:
            ProjectValidators.validate_code(code)
            self._code = code

        if description is not None:
            self._description = description

        if client_id is not None:
            self._client_id = client_id

        if status is not None:
            self._status = status

        if priority is not None:
            self._priority = priority

        # Validate date combination before applying to prevent inconsistent state
        new_start = start_date if start_date is not None else self._start_date
        new_end = end_date if end_date is not None else self._end_date

        ProjectValidators.validate_dates(new_start, new_end)

        if start_date is not None:
            self._start_date = start_date

        if end_date is not None:
            self._end_date = end_date

        self.mark_as_updated()

    def archive(self) -> None:
        """Archive the project."""
        self._status = ProjectStatus.ARCHIVED
        self.mark_as_updated()

    def complete(self) -> None:
        """Mark the project as completed."""
        self._status = ProjectStatus.COMPLETED
        self.mark_as_updated()

    def reactivate(self) -> None:
        """Reactivate an archived or completed project."""
        self._status = ProjectStatus.ACTIVE
        self.mark_as_updated()

    @classmethod
    def create(
        cls,
        name: str,
        code: str,
        created_by: EntityId,
        client_id: EntityId,
        description: str | None = None,
        priority: ProjectPriority | None = None,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> "ProjectEntity":
        """
        Factory method to create a new project.

        Args:
            name: Project name
            code: Project code (unique identifier)
            created_by: User ID of creator
            client_id: Client ID associated with project
            description: Optional description
            priority: Optional priority (defaults to MEDIUM)
            start_date: Optional start date
            end_date: Optional end date

        Returns:
            New ProjectEntity instance

        Raises:
            ValueError: If validation fails
        """
        now = datetime.now()
        return cls(
            id=EntityId.generate(),
            name=name,
            code=code,
            description=description,
            created_by=created_by,
            client_id=client_id,
            status=ProjectStatus.default(),
            priority=priority or ProjectPriority.default(),
            start_date=start_date,
            end_date=end_date,
            created_at=now,
            updated_at=now,
        )
