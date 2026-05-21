"""Story draft SQLAlchemy model."""
from datetime import datetime
from typing import Optional, List

from sqlalchemy import Column, String, Text, DateTime, ForeignKey, func, Index, ARRAY
from sqlalchemy.dialects.postgresql import UUID

from src.app.features.refinement.domain.value_objects.refinement_status import RefinementStatus
from src.app.shared.infrastructure.models.base_model import Base


class StoryDraftModel(Base):
    """
    SQLAlchemy model for story_drafts table.
    
    Maps to StoryDraftEntity in the domain layer.
    Stores both raw and AI-refined story content.
    """
    
    __tablename__ = "story_drafts"
    
    id = Column(UUID(as_uuid=True), primary_key=True)
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    acceptance_criteria = Column(ARRAY(Text), nullable=False, default=list)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    status = Column(
        String(20),
        nullable=False,
        default=RefinementStatus.DRAFT.value,
    )
    # Refined content from AI
    refined_title = Column(String(500), nullable=True)
    refined_description = Column(Text, nullable=True)
    refined_criteria = Column(ARRAY(Text), nullable=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    
    # Composite indexes for common query patterns
    __table_args__ = (
        Index('ix_story_drafts_project_id_created_at', 'project_id', 'created_at'),
        Index('ix_story_drafts_created_by_status', 'created_by', 'status'),
        Index('ix_story_drafts_status', 'status'),
    )
    
    def __repr__(self) -> str:
        """String representation of StoryDraftModel."""
        return f"<StoryDraftModel(id={self.id}, title='{self.title}', status='{self.status}')>"
