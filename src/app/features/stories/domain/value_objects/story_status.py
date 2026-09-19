"""Story status value object."""

from enum import StrEnum


class StoryStatus(StrEnum):
    """Story status enumeration."""

    TODO = "todo"
    IN_PROGRESS = "in_progress"
    BLOCKED = "blocked"
    DONE = "done"

    @classmethod
    def default(cls) -> "StoryStatus":
        """Get default status."""
        return cls.TODO
