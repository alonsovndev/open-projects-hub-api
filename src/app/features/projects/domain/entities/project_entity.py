"""Project entity - domain model for projects."""
from datetime import date, datetime
from typing import Optional

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
        description: Optional[str],
        created_by: EntityId,
        status: ProjectStatus,
        start_date: Optional[date],
        end_date: Optional[date],
        created_at: datetime,
        updated_at: datetime,
    ):
        """
        Initialize ProjectEntity.
        
        Args:
            id: Unique project identifier
            name: Project name (required, max 255 chars)
            description: Optional project description
            created_by: User ID of project creator
            status: Project status (active, completed, archived)
            start_date: Optional project start date
            end_date: Optional project end date
            created_at: Timestamp when project was created
            updated_at: Timestamp when project was last updated
            
        Raises:
            ValueError: If validation fails
        """
        self._validate_name(name)
        self._validate_dates(start_date, end_date)
        
        # Initialize base entity (id, created_at, updated_at)
        super().__init__(id=id, created_at=created_at, updated_at=updated_at)
        
        # Project-specific fields
        self._name = name
        self._description = description
        self._created_by = created_by
        self._status = status
        self._start_date = start_date
        self._end_date = end_date
    
    @staticmethod
    def _validate_name(name: str) -> None:
        """Validate project name."""
        if not name or not name.strip():
            raise ValueError("Project name cannot be empty")
        if len(name) > 255:
            raise ValueError("Project name cannot exceed 255 characters")
    
    @staticmethod
    def _validate_dates(start_date: Optional[date], end_date: Optional[date]) -> None:
        """Validate start and end dates."""
        if start_date and end_date and end_date < start_date:
            raise ValueError("End date cannot be before start date")
    
    @property
    def name(self) -> str:
        """Get project name."""
        return self._name
    
    @property
    def description(self) -> Optional[str]:
        """Get project description."""
        return self._description
    
    @property
    def created_by(self) -> EntityId:
        """Get creator user ID."""
        return self._created_by
    
    @property
    def status(self) -> ProjectStatus:
        """Get project status."""
        return self._status
    
    @property
    def start_date(self) -> Optional[date]:
        """Get project start date."""
        return self._start_date
    
    @property
    def end_date(self) -> Optional[date]:
        """Get project end date."""
        return self._end_date
    
    def update_details(
        self,
        name: Optional[str] = None,
        description: Optional[str] = None,
        status: Optional[ProjectStatus] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> None:
        """
        Update project details.
        
        Args:
            name: New project name (if provided)
            description: New description (if provided)
            status: New status (if provided)
            start_date: New start date (if provided)
            end_date: New end date (if provided)
            
        Raises:
            ValueError: If validation fails
        """
        if name is not None:
            self._validate_name(name)
            self._name = name
        
        if description is not None:
            self._description = description
        
        if status is not None:
            self._status = status
        
        # Handle date updates
        new_start = start_date if start_date is not None else self._start_date
        new_end = end_date if end_date is not None else self._end_date
        
        self._validate_dates(new_start, new_end)
        
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
        created_by: EntityId,
        description: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> "ProjectEntity":
        """
        Factory method to create a new project.
        
        Args:
            name: Project name
            created_by: User ID of creator
            description: Optional description
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
            description=description,
            created_by=created_by,
            status=ProjectStatus.default(),
            start_date=start_date,
            end_date=end_date,
            created_at=now,
            updated_at=now,
        )
