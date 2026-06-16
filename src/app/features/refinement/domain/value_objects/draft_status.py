"""Draft status value object."""

from enum import StrEnum


class DraftStatus(StrEnum):
    """Status of a story draft — either pending approval or already applied."""

    DRAFT = "draft"
    APPLIED = "applied"

    @classmethod
    def default(cls) -> "DraftStatus":
        """Return the default status for new drafts."""
        return cls.DRAFT
