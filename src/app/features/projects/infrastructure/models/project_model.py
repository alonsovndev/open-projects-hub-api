"""SQLAlchemy model for projects table."""

import uuid

from sqlalchemy import Column, Date, DateTime, Enum as SQLEnum, ForeignKey, Index, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

# Imported for relationship resolution
from src.app.features.clients.infrastructure.models.client_model import ClientModel  # noqa: F401
from src.app.features.projects.domain.value_objects.project_phase import ProjectPhase
from src.app.features.projects.domain.value_objects.project_priority import ProjectPriority
from src.app.features.projects.domain.value_objects.project_status import ProjectStatus
from src.app.shared.persistence import Base


class ProjectModel(Base):
    """
    SQLAlchemy model for projects table.

    Maps to ProjectEntity in the domain layer.
    """

    __tablename__ = "projects"

    # 1. Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # 2. Data columns
    name = Column(String(255), nullable=False)
    code = Column(String(50), nullable=False)
    description = Column(Text, nullable=True)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    workspace_id = Column(UUID(as_uuid=True), ForeignKey("workspaces.id", ondelete="RESTRICT"), nullable=False)
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
    phase = Column(
        SQLEnum(ProjectPhase, values_callable=lambda obj: [e.value for e in obj]),
        nullable=False,
        server_default=ProjectPhase.DISCOVERY.value,
        default=ProjectPhase.DISCOVERY.value,
    )
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)

    # Relationships
    client = relationship("ClientModel", backref="projects")
    stories = relationship("StoryModel", back_populates="project", lazy="selectin")

    # 3. Audit columns
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False, index=True
    )

    # Composite indexes for common query patterns
    __table_args__ = (
        # Index for filtering by status and ordering by created_at
        Index("ix_projects_status_created_at", "status", "created_at"),
        # Index for user's projects
        Index("ix_projects_created_by", "created_by"),
        # Index for filtering by priority
        Index("ix_projects_priority", "priority"),
        # Index for code lookup
        Index("ix_projects_code", "code"),
        # Index for client lookup
        Index("ix_projects_client_id", "client_id"),
        Index("ix_projects_workspace_id_status_created_at", "workspace_id", "status", "created_at"),
        # Codes are unique per workspace, not globally: two freelancers can both use "WEB".
        UniqueConstraint("workspace_id", "code", name="uq_projects_workspace_id_code"),
    )

    def __repr__(self) -> str:
        """String representation of ProjectModel."""
        return f"<ProjectModel(id={self.id}, code='{self.code}', name='{self.name}', status='{self.status}')>"
