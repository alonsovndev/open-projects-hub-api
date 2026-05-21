"""SQLAlchemy model for projects table."""
from datetime import date, datetime
from typing import Optional

from sqlalchemy import Column, String, Text, Date, DateTime, ForeignKey, Enum as SQLEnum, func, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from src.app.features.projects.domain.value_objects.project_status import ProjectStatus
from src.app.features.projects.domain.value_objects.project_priority import ProjectPriority
from src.app.shared.infrastructure.models.base_model import Base


class ProjectModel(Base):
    """
    SQLAlchemy model for projects table.
    
    Maps to ProjectEntity in the domain layer.
    """
    
    __tablename__ = "projects"
    
    id = Column(UUID(as_uuid=True), primary_key=True)
    name = Column(String(255), nullable=False)
    code = Column(String(50), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    client_id = Column(UUID(as_uuid=True), ForeignKey("clients.id"), nullable=False)
    status = Column(
        SQLEnum(ProjectStatus, values_callable=lambda obj: [e.value for e in obj]),
        nullable=False,
        default=ProjectStatus.ACTIVE.value,
    )
    priority = Column(
        SQLEnum(ProjectPriority, values_callable=lambda obj: [e.value for e in obj]),
        nullable=False,
        default=ProjectPriority.MEDIUM.value,
    )
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    client = relationship("ClientModel", backref="projects")
    
    # Composite indexes for common query patterns
    __table_args__ = (
        # Index for filtering by status and ordering by created_at
        Index('ix_projects_status_created_at', 'status', 'created_at'),
        # Index for user's projects
        Index('ix_projects_created_by', 'created_by'),
        # Index for filtering by priority
        Index('ix_projects_priority', 'priority'),
        # Index for code lookup
        Index('ix_projects_code', 'code'),
        # Index for client lookup (already created by migration)
        # Index('ix_projects_client_id', 'client_id'),
    )
    
    def __repr__(self) -> str:
        """String representation of ProjectModel."""
        return f"<ProjectModel(id={self.id}, code='{self.code}', name='{self.name}', status='{self.status}')>"
