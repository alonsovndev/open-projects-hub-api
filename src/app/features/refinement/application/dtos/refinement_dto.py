"""Data transfer objects for refinement operations."""

from collections.abc import Callable

from pydantic import BaseModel, ConfigDict, field_validator
from pydantic.alias_generators import to_camel

from src.app.features.ai_config.domain.value_objects.ai_provider import RefinementProvider
from src.app.features.refinement.domain.validators.refinement_validators import RefinementValidators
from src.app.features.stories.domain.validators.story_validators import StoryValidators
from src.app.shared.domain.exceptions.domain_exceptions import ValidationError


def _reject(validate: Callable[[], None]) -> None:
    """
    Run a domain validator and re-raise its failure as a ValueError.

    Pydantic only folds ValueError into a 422 field error; a domain ValidationError would
    escape to the global handler and surface as a 400 without naming the offending field.
    """
    try:
        validate()
    except ValidationError as e:
        raise ValueError(str(e)) from e


class GenerateStoriesRequest(BaseModel):
    """Request model for generating multiple stories from raw notes."""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

    project_id: str
    raw_notes: str
    # Which provider to charge this run to. Defaults to the platform's free credits so
    # existing callers keep working unchanged (EPIC-3 predates provider selection).
    provider: RefinementProvider = RefinementProvider.PLATFORM

    @field_validator("project_id")
    @classmethod
    def validate_project_id(cls, project_id: str) -> str:
        """Validate project ID using domain validators."""
        _reject(lambda: RefinementValidators.validate_project_id(project_id))
        return project_id.strip()

    @field_validator("raw_notes")
    @classmethod
    def validate_raw_notes(cls, raw_notes: str) -> str:
        """Validate raw notes using domain validators."""
        _reject(lambda: RefinementValidators.validate_raw_notes(raw_notes))
        return raw_notes.strip()


class GeneratedStoryResponse(BaseModel):
    """Response model for a single generated story."""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

    title: str
    description: str
    acceptance_criteria: list[str]


class GenerateStoriesResponse(BaseModel):
    """Response model for bulk story generation."""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

    stories: list[GeneratedStoryResponse]
    raw_notes: str
    # Non-zero when sanitization altered the notes before refining them, so the UI can say
    # so rather than leaving the Admin to wonder why output ignores part of their input.
    redaction_count: int = 0
    # Which provider actually served the run, echoed so the UI can label the result.
    provider: RefinementProvider = RefinementProvider.PLATFORM
    # Credits left after this run. None when a user's own key served it and no credit was
    # spent, which is how the UI knows to keep the balance display unchanged (FR-010-08).
    credits_remaining: int | None = None


class ApproveStoryRequest(BaseModel):
    """A refined story the Admin approved; it is saved to the backlog only now."""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

    project_id: str
    title: str
    description: str | None = None
    acceptance_criteria: list[str] = []

    @field_validator("project_id")
    @classmethod
    def validate_project_id(cls, project_id: str) -> str:
        """Validate project ID using domain validators."""
        _reject(lambda: RefinementValidators.validate_project_id(project_id))
        return project_id.strip()

    @field_validator("title")
    @classmethod
    def validate_title(cls, title: str) -> str:
        """Validate against the stories table's own limits, which are tighter than the AI draft's."""
        _reject(lambda: StoryValidators.validate_title(title))
        return title.strip()

    @field_validator("acceptance_criteria")
    @classmethod
    def validate_acceptance_criteria(cls, acceptance_criteria: list[str]) -> list[str]:
        """Validate acceptance criteria the same way manual story creation does."""
        _reject(lambda: StoryValidators.validate_acceptance_criteria(acceptance_criteria))
        return acceptance_criteria


class ApproveStoriesBulkRequest(BaseModel):
    """Request model for approving several refined stories at once."""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

    stories: list[ApproveStoryRequest]

    @field_validator("stories")
    @classmethod
    def validate_stories(cls, stories: list[ApproveStoryRequest]) -> list[ApproveStoryRequest]:
        """Require at least one story."""
        if not stories:
            raise ValueError("At least one story is required")
        return stories


class BulkApprovedStory(BaseModel):
    """Lightweight reference to a story created from bulk approval."""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

    id: str
    title: str


class ApproveStoriesBulkResponse(BaseModel):
    """Response model for bulk approve operation."""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

    approved_count: int
    stories: list[BulkApprovedStory]
