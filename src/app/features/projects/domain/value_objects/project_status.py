"""Project status value object."""

from enum import StrEnum


class ProjectStatus(StrEnum):
    """Project status enumeration."""

    ACTIVE = "active"
    COMPLETED = "completed"
    ARCHIVED = "archived"

    @classmethod
    def default(cls) -> "ProjectStatus":
        """Return default status for new projects."""
        return cls.ACTIVE
