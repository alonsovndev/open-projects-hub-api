"""Mapper for dashboard DTOs."""

from src.app.features.dashboard.application.dtos.dashboard_dto import (
    DashboardStatsResponse,
    ProjectSummary,
    StorySummary,
)
from src.app.features.projects.domain.entities.project_entity import ProjectEntity
from src.app.features.stories.domain.entities.story_entity import StoryEntity


def to_project_summary(project: ProjectEntity) -> ProjectSummary:
    """Convert a ProjectEntity to a ProjectSummary DTO."""
    return ProjectSummary(
        id=str(project.id),
        name=project.name,
        status=project.status.value,
        created_at=project.created_at.isoformat(),
    )


def to_story_summary(story: StoryEntity) -> StorySummary:
    """Convert a StoryEntity to a StorySummary DTO."""
    return StorySummary(
        id=str(story.id),
        title=story.title,
        status=story.status.value,
        priority=story.priority.value,
        created_at=story.created_at.isoformat(),
    )


def to_dashboard_stats_response(
    stats: dict,
    recent_projects: list[ProjectSummary],
    recent_stories: list[StorySummary],
) -> DashboardStatsResponse:
    """Build a DashboardStatsResponse from raw stats and mapped summaries."""
    return DashboardStatsResponse(
        total_projects=stats["total_projects"],
        active_projects=stats["active_projects"],
        total_stories=stats["total_stories"],
        assigned_stories=stats["assigned_stories"],
        completed_stories=stats["completed_stories"],
        recent_projects=recent_projects,
        recent_stories=recent_stories,
    )
