"""Project phase value object."""

from enum import StrEnum


class ProjectPhase(StrEnum):
    """Project phase enumeration. MVP supports discovery and planning only."""

    DISCOVERY = "discovery"
    PLANNING = "planning"

    @classmethod
    def default(cls) -> "ProjectPhase":
        """Return default phase for new projects."""
        return cls.DISCOVERY
