"""Data transfer objects for refinement operations."""
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, field_validator
from pydantic.alias_generators import to_camel

from src.app.features.refinement.domain.validators.refinement_validators import RefinementValidators


class UpdateStoryDraftRequest(BaseModel):
    """Request model for updating a story draft."""
    
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )
    
    title: Optional[str] = None
    description: Optional[str] = None
    acceptance_criteria: Optional[List[str]] = None
    
    @field_validator("title")
    @classmethod
    def validate_title(cls, v: Optional[str]) -> Optional[str]:
        """Validate story title using domain validators."""
        if v is not None:
            RefinementValidators.validate_title(v)
            return v.strip()
        return v


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
    def validate_project_id(cls, v: str) -> str:
        """Validate project ID using domain validators."""
        RefinementValidators.validate_project_id(v)
        return v.strip()
    
    @field_validator("raw_notes")
    @classmethod
    def validate_raw_notes(cls, v: str) -> str:
        """Validate raw notes using domain validators."""
        RefinementValidators.validate_raw_notes(v)
        return v.strip()


class GeneratedStoryResponse(BaseModel):
    """Response model for a single generated story."""
    
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )
    
    id: str  # Draft ID
    title: str
    description: str
    acceptance_criteria: List[str]
    confidence: float


class GenerateStoriesResponse(BaseModel):
    """Response model for bulk story generation."""
    
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )
    
    stories: List[GeneratedStoryResponse]
    raw_notes: str


class ApproveDraftsBulkRequest(BaseModel):
    """Request model for bulk approving drafts."""
    
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )
    
    draft_ids: List[str]
    
    @field_validator("draft_ids")
    @classmethod
    def validate_draft_ids(cls, v: List[str]) -> List[str]:
        """Validate draft IDs."""
        if not v or len(v) == 0:
            raise ValueError("At least one draft ID is required")
        return v


class ApproveDraftsBulkResponse(BaseModel):
    """Response model for bulk approve operation."""
    
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )
    
    approved_count: int
    stories: List[dict]  # List of created story IDs and titles
