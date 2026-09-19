"""Dashboard DTOs for stats."""

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


class ProjectSummary(BaseModel):
    """DTO for recent project summary."""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

    id: str
    name: str
    status: str
    created_at: str


class StorySummary(BaseModel):
    """DTO for recent story summary."""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

    id: str
    title: str
    status: str
    priority: str
    created_at: str


class DashboardStatsResponse(BaseModel):
    """DTO for dashboard statistics response."""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

    total_projects: int
    active_projects: int
    total_stories: int
    assigned_stories: int
    completed_stories: int
    recent_projects: list[ProjectSummary] = Field(default_factory=list)
    recent_stories: list[StorySummary] = Field(default_factory=list)
