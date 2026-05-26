"""Project status value object."""

from enum import Enum


class ProjectStatus(str, Enum):
    """Project status enumeration."""

    ACTIVE = "active"
    COMPLETED = "completed"
    ARCHIVED = "archived"

    @classmethod
    def default(cls) -> "ProjectStatus":
        """Return default status for new projects."""
        return cls.ACTIVE
