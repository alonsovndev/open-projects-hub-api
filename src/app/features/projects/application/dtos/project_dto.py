"""Data transfer objects for project operations."""
from datetime import date
from typing import Optional

from pydantic import BaseModel, field_validator, model_validator, ConfigDict
from pydantic.alias_generators import to_camel

from src.app.features.projects.domain.validators.project_validators import ProjectValidators
from src.app.features.projects.domain.value_objects.project_status import ProjectStatus
from src.app.features.projects.domain.value_objects.project_priority import ProjectPriority


class ProjectResponse(BaseModel):
    """Response model for project data."""
    
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )
    
    id: str
    name: str
    code: str
    description: Optional[str]
    created_by: str
    client_id: str
    client_name: str
    status: str
    priority: str
    start_date: Optional[date]
    end_date: Optional[date]
    created_at: str
    updated_at: str
    stories_count: int = 0
    completed_stories: int = 0


class CreateProjectRequest(BaseModel):
    """Request model for creating a project."""
    
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )
    
    name: str
    code: str
    client_id: str
    description: Optional[str] = None
    priority: Optional[str] = "medium"
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    
    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate project name."""
        ProjectValidators.validate_name(v)
        return v
    
    @field_validator("code")
    @classmethod
    def validate_code(cls, v: str) -> str:
        """Validate project code."""
        ProjectValidators.validate_code(v)
        return v
    
    @field_validator("priority")
    @classmethod
    def validate_priority(cls, v: Optional[str]) -> Optional[str]:
        """Validate priority if provided."""
        if v is not None:
            valid_priorities = [p.value for p in ProjectPriority]
            if v not in valid_priorities:
                raise ValueError(f"Priority must be one of: {', '.join(valid_priorities)}")
        return v
    
    @model_validator(mode='after')
    def validate_date_range(self) -> 'CreateProjectRequest':
        """Validate that end_date is not before start_date."""
        if self.start_date and self.end_date:
            ProjectValidators.validate_dates(self.start_date, self.end_date)
        return self


class UpdateProjectRequest(BaseModel):
    """Request model for updating a project."""
    
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )
    
    name: Optional[str] = None
    code: Optional[str] = None
    client_id: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    
    @field_validator("name")
    @classmethod
    def validate_name(cls, v: Optional[str]) -> Optional[str]:
        """Validate project name if provided."""
        if v is not None:
            ProjectValidators.validate_name(v)
        return v
    
    @field_validator("code")
    @classmethod
    def validate_code(cls, v: Optional[str]) -> Optional[str]:
        """Validate project code if provided."""
        if v is not None:
            ProjectValidators.validate_code(v)
        return v
    
    @field_validator("status")
    @classmethod
    def validate_status(cls, v: Optional[str]) -> Optional[str]:
        """Validate status if provided."""
        if v is not None:
            valid_statuses = [s.value for s in ProjectStatus]
            if v not in valid_statuses:
                raise ValueError(f"Status must be one of: {', '.join(valid_statuses)}")
        return v
    
    @field_validator("priority")
    @classmethod
    def validate_priority(cls, v: Optional[str]) -> Optional[str]:
        """Validate priority if provided."""
        if v is not None:
            valid_priorities = [p.value for p in ProjectPriority]
            if v not in valid_priorities:
                raise ValueError(f"Priority must be one of: {', '.join(valid_priorities)}")
        return v
    
    @model_validator(mode='after')
    def validate_date_range(self) -> 'UpdateProjectRequest':
        """Validate that end_date is not before start_date."""
        if self.start_date and self.end_date:
            ProjectValidators.validate_dates(self.start_date, self.end_date)
        return self
