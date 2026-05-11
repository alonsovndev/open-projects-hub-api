"""SQLAlchemy model for projects table."""
from datetime import date, datetime
from typing import Optional

from sqlalchemy import Column, String, Text, Date, DateTime, ForeignKey, Enum as SQLEnum, func, Index
from sqlalchemy.dialects.postgresql import UUID

from src.app.features.projects.domain.value_objects.project_status import ProjectStatus
from src.app.shared.infrastructure.models.base_model import Base


class ProjectModel(Base):
    """
    SQLAlchemy model for projects table.
    
    Maps to ProjectEntity in the domain layer.
    """
    
    __tablename__ = "projects"
    
    id = Column(UUID(as_uuid=True), primary_key=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    status = Column(
        SQLEnum(ProjectStatus, values_callable=lambda obj: [e.value for e in obj]),
        nullable=False,
        default=ProjectStatus.ACTIVE.value,
    )
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    
    # Composite indexes for common query patterns
    __table_args__ = (
        # Index for filtering by status and ordering by created_at
        Index('ix_projects_status_created_at', 'status', 'created_at'),
        # Index for user's projects
        Index('ix_projects_created_by', 'created_by'),
    )
    
    def __repr__(self) -> str:
        """String representation of ProjectModel."""
        return f"<ProjectModel(id={self.id}, name='{self.name}', status='{self.status}')>"
