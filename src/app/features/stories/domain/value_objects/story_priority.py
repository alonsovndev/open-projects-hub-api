"""Story priority value object."""

from enum import StrEnum


class StoryPriority(StrEnum):
    """Story priority enumeration."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

    @classmethod
    def default(cls) -> "StoryPriority":
        """Get default priority."""
        return cls.MEDIUM
