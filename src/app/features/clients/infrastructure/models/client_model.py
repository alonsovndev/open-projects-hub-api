"""Client SQLAlchemy model."""

from sqlalchemy import Column, DateTime, String, Text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.sql import func

from src.app.shared.persistence.base_model import Base


class ClientModel(Base):
    """SQLAlchemy model for clients table."""

    __tablename__ = "clients"

    id = Column(PGUUID(as_uuid=True), primary_key=True)
    name = Column(String(200), nullable=False, index=True)
    email = Column(String(255), nullable=True, index=True)
    phone = Column(String(50), nullable=True)
    company = Column(String(200), nullable=True, index=True)
    address = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    def __repr__(self) -> str:
        return f"<ClientModel(id={self.id}, name={self.name}, company={self.company})>"
