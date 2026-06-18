"""Client SQLAlchemy model."""

import uuid

from sqlalchemy import Column, DateTime, String, Text, func
from sqlalchemy.dialects.postgresql import UUID

from src.app.shared.persistence import Base


class ClientModel(Base):
    """SQLAlchemy model for clients table."""

    __tablename__ = "clients"

    # 1. Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # 2. Data columns
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

    def __repr__(self) -> str:
        return f"<ClientModel(id={self.id}, name={self.name}, company={self.company})>"
