"""Story DTOs for request and response."""

from pydantic import BaseModel, ConfigDict, field_validator
from pydantic.alias_generators import to_camel

from src.app.features.stories.domain.validators.story_validators import StoryValidators
from src.app.features.stories.domain.value_objects.story_priority import StoryPriority
from src.app.features.stories.domain.value_objects.story_status import StoryStatus
from src.app.shared.domain.exceptions.domain_exceptions import ValidationError


class CreateStoryRequest(BaseModel):
    """DTO for creating a story."""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

    title: str
    description: str | None = None
    project_id: str
    priority: str | None = "medium"
    points: int | None = None

    @field_validator("title")
    @classmethod
    def validate_title(cls, title: str) -> str:
        """Validate story title."""
        StoryValidators.validate_title(title)
        return title

    @field_validator("priority")
    @classmethod
    def validate_priority(cls, priority: str | None) -> str | None:
        """Validate priority if provided."""
        if priority is not None:
            valid_priorities = [p.value for p in StoryPriority]
            if priority not in valid_priorities:
                raise ValidationError(f"Priority must be one of: {', '.join(valid_priorities)}")
        return priority

    @field_validator("points")
    @classmethod
    def validate_points(cls, points: int | None) -> int | None:
        """Validate story points if provided."""
        if points is not None:
            StoryValidators.validate_points(points)
        return points


class UpdateStoryRequest(BaseModel):
    """DTO for updating a story."""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

    title: str | None = None
    description: str | None = None
    status: str | None = None
    priority: str | None = None
    points: int | None = None

    @field_validator("title")
    @classmethod
    def validate_title(cls, title: str | None) -> str | None:
        """Validate story title if provided."""
        if title is not None:
            StoryValidators.validate_title(title)
        return title

    @field_validator("status")
    @classmethod
    def validate_status(cls, status: str | None) -> str | None:
        """Validate status if provided."""
        if status is not None:
            valid_statuses = [s.value for s in StoryStatus]
            if status not in valid_statuses:
                raise ValidationError(f"Status must be one of: {', '.join(valid_statuses)}")
        return status

    @field_validator("priority")
    @classmethod
    def validate_priority(cls, priority: str | None) -> str | None:
        """Validate priority if provided."""
        if priority is not None:
            valid_priorities = [p.value for p in StoryPriority]
            if priority not in valid_priorities:
                raise ValidationError(f"Priority must be one of: {', '.join(valid_priorities)}")
        return priority

    @field_validator("points")
    @classmethod
    def validate_points(cls, points: int | None) -> int | None:
        """Validate story points if provided."""
        if points is not None:
            StoryValidators.validate_points(points)
        return points


class AssignStoryRequest(BaseModel):
    """DTO for assigning a story to a user."""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

    user_id: str


class StoryResponse(BaseModel):
    """DTO for story response."""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

    id: str
    title: str
    description: str | None
    project_id: str
    created_by: str
    assigned_to: str | None
    status: str
    priority: str
    points: int | None
    created_at: str
    updated_at: str
