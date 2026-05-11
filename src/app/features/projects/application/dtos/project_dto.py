"""Data transfer objects for project operations."""
from datetime import date
from typing import Optional

from pydantic import BaseModel, field_validator, ConfigDict
from pydantic.alias_generators import to_camel


class ProjectResponse(BaseModel):
    """Response model for project data."""
    
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )
    
    id: str
    name: str
    description: Optional[str]
    created_by: str
    status: str
    start_date: Optional[date]
    end_date: Optional[date]
    created_at: str
    updated_at: str


class CreateProjectRequest(BaseModel):
    """Request model for creating a project."""
    
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )
    
    name: str
    description: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    
    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate project name."""
        if not v or not v.strip():
            raise ValueError("Project name cannot be empty")
        if len(v) > 255:
            raise ValueError("Project name cannot exceed 255 characters")
        return v


class UpdateProjectRequest(BaseModel):
    """Request model for updating a project."""
    
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )
    
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    
    @field_validator("name")
    @classmethod
    def validate_name(cls, v: Optional[str]) -> Optional[str]:
        """Validate project name if provided."""
        if v is not None:
            if not v.strip():
                raise ValueError("Project name cannot be empty")
            if len(v) > 255:
                raise ValueError("Project name cannot exceed 255 characters")
        return v
    
    @field_validator("status")
    @classmethod
    def validate_status(cls, v: Optional[str]) -> Optional[str]:
        """Validate status if provided."""
        if v is not None:
            valid_statuses = ["active", "completed", "archived"]
            if v not in valid_statuses:
                raise ValueError(f"Status must be one of: {', '.join(valid_statuses)}")
        return v
