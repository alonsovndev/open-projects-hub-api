"""Data transfer objects for refinement operations."""

from pydantic import BaseModel, ConfigDict, field_validator
from pydantic.alias_generators import to_camel

from src.app.features.refinement.domain.validators.refinement_validators import RefinementValidators


class UpdateStoryDraftRequest(BaseModel):
    """Request model for updating a story draft."""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

    title: str | None = None
    description: str | None = None
    acceptance_criteria: list[str] | None = None

    @field_validator("title")
    @classmethod
    def validate_title(cls, title: str | None) -> str | None:
        """Validate story title using domain validators."""
        if title is not None:
            RefinementValidators.validate_title(title)
            return title.strip()
        return title


class GenerateStoriesRequest(BaseModel):
    """Request model for generating multiple stories from raw notes."""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

    project_id: str
    raw_notes: str

    @field_validator("project_id")
    @classmethod
    def validate_project_id(cls, project_id: str) -> str:
        """Validate project ID using domain validators."""
        RefinementValidators.validate_project_id(project_id)
        return project_id.strip()

    @field_validator("raw_notes")
    @classmethod
    def validate_raw_notes(cls, raw_notes: str) -> str:
        """Validate raw notes using domain validators."""
        RefinementValidators.validate_raw_notes(raw_notes)
        return raw_notes.strip()


class GeneratedStoryResponse(BaseModel):
    """Response model for a single generated story."""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

    id: str  # Draft ID
    title: str
    description: str
    acceptance_criteria: list[str]
    confidence: float


class GenerateStoriesResponse(BaseModel):
    """Response model for bulk story generation."""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

    stories: list[GeneratedStoryResponse]
    raw_notes: str


class ApproveDraftsBulkRequest(BaseModel):
    """Request model for bulk approving drafts."""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

    draft_ids: list[str]

    @field_validator("draft_ids")
    @classmethod
    def validate_draft_ids(cls, draft_ids: list[str]) -> list[str]:
        """Validate draft IDs."""
        if not draft_ids or len(draft_ids) == 0:
            raise ValueError("At least one draft ID is required")
        return draft_ids


class ApproveDraftsBulkResponse(BaseModel):
    """Response model for bulk approve operation."""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

    approved_count: int
    stories: list[dict]  # List of created story IDs and titles
