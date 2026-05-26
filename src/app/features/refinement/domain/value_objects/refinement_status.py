"""Refinement status value object."""

from enum import Enum


class RefinementStatus(str, Enum):
    """Status of a story draft in the refinement process."""

    DRAFT = "draft"
    REFINING = "refining"
    REFINED = "refined"
    APPLIED = "applied"

    @classmethod
    def default(cls) -> "RefinementStatus":
        """Return the default status for new drafts."""
        return cls.DRAFT
