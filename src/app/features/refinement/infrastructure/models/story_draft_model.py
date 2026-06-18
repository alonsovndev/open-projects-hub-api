"""Story draft SQLAlchemy model."""

import uuid

from sqlalchemy import ARRAY, Column, DateTime, Enum as SQLEnum, ForeignKey, Index, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from src.app.features.refinement.domain.value_objects.draft_status import DraftStatus
from src.app.shared.persistence import Base


class StoryDraftModel(Base):
    """
    SQLAlchemy model for story_drafts table.

    Maps to StoryDraftEntity in the domain layer.
    Stores both raw and AI-refined story content.
    """

    __tablename__ = "story_drafts"

    # 1. Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # 2. Data columns
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    acceptance_criteria = Column(ARRAY(Text), nullable=False, default=list)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    status = Column(
        SQLEnum(DraftStatus, values_callable=lambda obj: [e.value for e in obj]),
        nullable=False,
        default=DraftStatus.DRAFT.value,
    )

    # Relationships
    project = relationship("ProjectModel", back_populates="story_drafts", lazy="selectin")

    # 3. Audit columns
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False, index=True
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
