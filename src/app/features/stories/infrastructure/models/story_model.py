"""SQLAlchemy model for stories table."""

from sqlalchemy import Column, String, Text, Integer, DateTime, ForeignKey, Enum as SQLEnum, func, Index
from sqlalchemy.dialects.postgresql import UUID

from src.app.features.stories.domain.value_objects.story_priority import StoryPriority
from src.app.features.stories.domain.value_objects.story_status import StoryStatus
from src.app.shared.persistence.base_model import Base


class StoryModel(Base):
    """
    SQLAlchemy model for stories table.
    
    Maps to StoryEntity in the domain layer.
    """
    
    __tablename__ = "stories"
    
    id = Column(UUID(as_uuid=True), primary_key=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    assigned_to = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    status = Column(
        SQLEnum(StoryStatus, values_callable=lambda obj: [e.value for e in obj]),
        nullable=False,
        default=StoryStatus.TODO.value,
    )
    priority = Column(
        SQLEnum(StoryPriority, values_callable=lambda obj: [e.value for e in obj]),
        nullable=False,
        default=StoryPriority.MEDIUM.value,
    )
    points = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    
    # Composite indexes for common query patterns
    __table_args__ = (
        # Index for project stories
        Index('ix_stories_project_id_created_at', 'project_id', 'created_at'),
        # Index for user's assigned stories
        Index('ix_stories_assigned_to_status', 'assigned_to', 'status'),
        # Index for filtering by status and priority
        Index('ix_stories_status_priority', 'status', 'priority'),
        # Index for created_by user
        Index('ix_stories_created_by', 'created_by'),
    )
    
    def __repr__(self) -> str:
        """String representation of StoryModel."""
        return f"<StoryModel(id={self.id}, title='{self.title}', status='{self.status}')>"