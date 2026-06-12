"""Client SQLAlchemy model."""

from sqlalchemy import Column, String, Text

from src.app.shared.persistence.base_model import BaseModel


class ClientModel(BaseModel):
    """SQLAlchemy model for clients table."""

    __tablename__ = "clients"

    name = Column(String(200), nullable=False, index=True)
    email = Column(String(255), nullable=True, index=True)
    phone = Column(String(50), nullable=True)
    company = Column(String(200), nullable=True, index=True)
    address = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)

    def __repr__(self) -> str:
        return f"<ClientModel(id={self.id}, name={self.name}, company={self.company})>"
