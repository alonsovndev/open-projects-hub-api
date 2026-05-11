"""Story priority value object."""
from enum import Enum


class StoryPriority(str, Enum):
    """Story priority enumeration."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

    @classmethod
    def default(cls) -> "StoryPriority":
        """Get default priority."""
        return cls.MEDIUM

    def __str__(self) -> str:
        """Return string value."""
        return self.value