"""Story status value object."""
from enum import Enum


class StoryStatus(str, Enum):
    """Story status enumeration."""

    TODO = "todo"
    IN_PROGRESS = "in_progress"
    DONE = "done"

    @classmethod
    def default(cls) -> "StoryStatus":
        """Get default status."""
        return cls.TODO

    def __str__(self) -> str:
        """Return string value."""
        return self.value