"""Project priority value object."""

from enum import StrEnum


class ProjectPriority(StrEnum):
    """Project priority enumeration."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

    @classmethod
    def default(cls) -> "ProjectPriority":
        """Return default priority for new projects."""
        return cls.MEDIUM
