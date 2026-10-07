"""Workspace SQLAlchemy model."""

import uuid

from sqlalchemy import Column, DateTime, Integer, String, func
from sqlalchemy.dialects.postgresql import UUID

from src.app.shared.persistence import Base


class WorkspaceModel(Base):
    __tablename__ = "workspaces"

    # 1. Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # 2. Data columns
    name = Column(String(100), nullable=False)
    # Lifetime total of free AI credits handed to users; never decreases, so removing and
    # re-adding members cannot mint more.
    ai_credits_granted_total = Column(Integer, nullable=False, default=0, server_default="0")

    # 3. Audit columns
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
