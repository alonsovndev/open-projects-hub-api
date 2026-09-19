"""Data transfer objects for project operations."""

from datetime import date

from pydantic import BaseModel, ConfigDict, field_validator, model_validator
from pydantic.alias_generators import to_camel

from src.app.features.projects.domain.validators.project_validators import ProjectValidators
from src.app.features.projects.domain.value_objects.project_phase import ProjectPhase
from src.app.features.projects.domain.value_objects.project_priority import ProjectPriority
from src.app.shared.domain.exceptions.domain_exceptions import ValidationError


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
    phase: str
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
    phase: str
    description: str | None = None
    priority: str | None = "medium"
    start_date: date | None = None
    end_date: date | None = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, name: str) -> str:
        """Validate project name."""
        ProjectValidators.validate_name(name)
        return name

    @field_validator("code")
    @classmethod
    def validate_code(cls, code: str) -> str:
        """Validate project code."""
        ProjectValidators.validate_code(code)
        return code

    @field_validator("priority")
    @classmethod
    def validate_priority(cls, priority: str | None) -> str | None:
        """Validate priority if provided."""
        if priority is not None:
            valid_priorities = [p.value for p in ProjectPriority]
            if priority not in valid_priorities:
                raise ValidationError(f"Priority must be one of: {', '.join(valid_priorities)}")
        return priority

    @field_validator("phase")
    @classmethod
    def validate_phase(cls, phase: str) -> str:
        """Validate phase (MVP supports discovery and planning only)."""
        valid_phases = [p.value for p in ProjectPhase]
        if phase not in valid_phases:
            raise ValidationError(f"Phase must be one of: {', '.join(valid_phases)}")
        return phase

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
    priority: str | None = None
    start_date: date | None = None
    end_date: date | None = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, name: str | None) -> str | None:
        """Validate project name if provided."""
        if name is not None:
            ProjectValidators.validate_name(name)
        return name

    @field_validator("code")
    @classmethod
    def validate_code(cls, code: str | None) -> str | None:
        """Validate project code if provided."""
        if code is not None:
            ProjectValidators.validate_code(code)
        return code

    @field_validator("priority")
    @classmethod
    def validate_priority(cls, priority: str | None) -> str | None:
        """Validate priority if provided."""
        if priority is not None:
            valid_priorities = [p.value for p in ProjectPriority]
            if priority not in valid_priorities:
                raise ValidationError(f"Priority must be one of: {', '.join(valid_priorities)}")
        return priority

    @model_validator(mode="after")
    def validate_date_range(self) -> "UpdateProjectRequest":
        """Validate that end_date is not before start_date."""
        if self.start_date and self.end_date:
            ProjectValidators.validate_dates(self.start_date, self.end_date)
        return self
