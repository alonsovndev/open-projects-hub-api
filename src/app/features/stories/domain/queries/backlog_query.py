"""Query object describing a slice of a project's backlog."""

from dataclasses import dataclass
from datetime import date
from uuid import UUID

from src.app.features.stories.domain.value_objects.story_status import StoryStatus


@dataclass(frozen=True)
class BacklogQuery:
    """
    The scope of a backlog read: which project, which stories, how many.

    Grouped into one object rather than added as parameters to the repository port,
    which already carries six and is read by both the backlog view and the export.

    Attributes:
        project_id: The project whose backlog is being read
        workspace_id: The caller's workspace; stories of another workspace never match
        status: Optional story-status filter
        created_from: Include stories created on or after this date
        created_to: Include stories created on or before this date
        limit: Maximum number of stories to return
        offset: Number of stories to skip
    """

    project_id: UUID
    workspace_id: UUID
    status: StoryStatus | None = None
    created_from: date | None = None
    created_to: date | None = None
    limit: int = 50
    offset: int = 0
