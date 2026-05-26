"""Data transfer objects for project operations."""

from datetime import date

from pydantic import BaseModel, ConfigDict, field_validator, model_validator
from pydantic.alias_generators import to_camel

from src.app.features.projects.domain.validators.project_validators import ProjectValidators
from src.app.features.projects.domain.value_objects.project_priority import ProjectPriority
from src.app.features.projects.domain.value_objects.project_status import ProjectStatus


class ProjectResponse(BaseModel):
    """Response model for project data."""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

    id: str
    name: str
    code: str
    description: str | None
    created_by: str
    client_id: str
    client_name: str
    status: str
    priority: str
    start_date: date | None
    end_date: date | None
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
    description: str | None = None
    priority: str | None = "medium"
    start_date: date | None = None
    end_date: date | None = None

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
    def validate_priority(cls, v: str | None) -> str | None:
        """Validate priority if provided."""
        if v is not None:
            valid_priorities = [p.value for p in ProjectPriority]
            if v not in valid_priorities:
                raise ValueError(f"Priority must be one of: {', '.join(valid_priorities)}")
        return v

    @model_validator(mode="after")
    def validate_date_range(self) -> "CreateProjectRequest":
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

    name: str | None = None
    code: str | None = None
    client_id: str | None = None
    description: str | None = None
    status: str | None = None
    priority: str | None = None
    start_date: date | None = None
    end_date: date | None = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str | None) -> str | None:
        """Validate project name if provided."""
        if v is not None:
            ProjectValidators.validate_name(v)
        return v

    @field_validator("code")
    @classmethod
    def validate_code(cls, v: str | None) -> str | None:
        """Validate project code if provided."""
        if v is not None:
            ProjectValidators.validate_code(v)
        return v

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str | None) -> str | None:
        """Validate status if provided."""
        if v is not None:
            valid_statuses = [s.value for s in ProjectStatus]
            if v not in valid_statuses:
                raise ValueError(f"Status must be one of: {', '.join(valid_statuses)}")
        return v

    @field_validator("priority")
    @classmethod
    def validate_priority(cls, v: str | None) -> str | None:
        """Validate priority if provided."""
        if v is not None:
            valid_priorities = [p.value for p in ProjectPriority]
            if v not in valid_priorities:
                raise ValueError(f"Priority must be one of: {', '.join(valid_priorities)}")
        return v

    @model_validator(mode="after")
    def validate_date_range(self) -> "UpdateProjectRequest":
        """Validate that end_date is not before start_date."""
        if self.start_date and self.end_date:
            ProjectValidators.validate_dates(self.start_date, self.end_date)
        return self
