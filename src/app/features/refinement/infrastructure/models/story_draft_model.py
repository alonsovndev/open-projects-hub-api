"""Story draft SQLAlchemy model."""

from sqlalchemy import ARRAY, Column, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import UUID

from src.app.features.refinement.domain.value_objects.draft_status import DraftStatus
from src.app.shared.persistence.base_model import BaseModel


class StoryDraftModel(BaseModel):
    """
    SQLAlchemy model for story_drafts table.

    Maps to StoryDraftEntity in the domain layer.
    Stores both raw and AI-refined story content.
    """

    __tablename__ = "story_drafts"

    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    acceptance_criteria = Column(ARRAY(Text), nullable=False, default=list)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    status = Column(
        String(20),
        nullable=False,
        default=DraftStatus.DRAFT.value,
    )

    # Composite indexes for common query patterns
    __table_args__ = (
        Index("ix_story_drafts_project_id_created_at", "project_id", "created_at"),
        Index("ix_story_drafts_created_by_status", "created_by", "status"),
        Index("ix_story_drafts_status", "status"),
    )

    def __repr__(self) -> str:
        """String representation of StoryDraftModel."""
        return f"<StoryDraftModel(id={self.id}, title='{self.title}', status='{self.status}')>"
