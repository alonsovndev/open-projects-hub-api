"""Workspace DTOs."""

from pydantic import BaseModel, ConfigDict, field_validator
from pydantic.alias_generators import to_camel

from src.app.features.workspaces.domain.entities.workspace_entity import WORKSPACE_NAME_MAX_LENGTH


class UpdateWorkspaceRequest(BaseModel):
    """Request DTO for renaming the caller's workspace."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    name: str

    @field_validator("name")
    @classmethod
    def validate_name(cls, name: str) -> str:
        cleaned_name = name.strip()
        if not cleaned_name or len(cleaned_name) > WORKSPACE_NAME_MAX_LENGTH:
            raise ValueError(f"Workspace name must be 1-{WORKSPACE_NAME_MAX_LENGTH} characters")
        return cleaned_name


class WorkspaceResponse(BaseModel):
    """Response DTO for workspace data."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    id: str
    name: str
