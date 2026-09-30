"""Client SQLAlchemy model."""

import uuid

from sqlalchemy import Column, DateTime, ForeignKey, Index, String, Text, func, text
from sqlalchemy.dialects.postgresql import UUID

# Imported so the workspaces FK resolves whichever model module loads first
from src.app.features.workspaces.infrastructure.models.workspace_model import WorkspaceModel  # noqa: F401
from src.app.shared.persistence import Base


class ClientModel(Base):
    """SQLAlchemy model for clients table."""

    __tablename__ = "clients"

    # 1. Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # 2. Data columns
    workspace_id = Column(UUID(as_uuid=True), ForeignKey("workspaces.id", ondelete="RESTRICT"), nullable=False)
    name = Column(String(200), nullable=False, index=True)
    email = Column(String(255), nullable=True, index=True)
    phone = Column(String(50), nullable=True)
    company = Column(String(200), nullable=True, index=True)
    address = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)

    # 3. Audit columns
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False, index=True
    )

    __table_args__ = (
        Index("ix_clients_workspace_id_name", "workspace_id", "name"),
        # Client emails are unique within a workspace; the use cases check first, this closes the race.
        Index(
            "uq_clients_workspace_id_email",
            "workspace_id",
            "email",
            unique=True,
            postgresql_where=text("email IS NOT NULL"),
        ),
    )

    def __repr__(self) -> str:
        return f"<ClientModel(id={self.id}, name={self.name}, company={self.company})>"
