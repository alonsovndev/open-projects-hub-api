"""Project priority value object."""

from enum import Enum


class ProjectPriority(str, Enum):
    """Project priority enumeration."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

    @classmethod
    def default(cls) -> "ProjectPriority":
        """Return default priority for new projects."""
        return cls.MEDIUM
