"""
UserPreferences SQLAlchemy model.
"""
from sqlalchemy import Column, String, ForeignKey, DateTime, func
from sqlalchemy.dialects.postgresql import UUID

from src.app.shared.infrastructure.models.base_model import Base


class UserPreferencesModel(Base):
    """
    SQLAlchemy model for user_preferences table.
    
    Columns:
        id: Primary key (UUID)
        user_id: Foreign key to users table (UUID)
        theme: Theme preference (light | dark | auto)
        language: ISO language code (e.g., "en")
        created_at: Timestamp when record was created
        updated_at: Timestamp when record was last updated
    """

    __tablename__ = "user_preferences"

    id = Column(UUID(as_uuid=True), primary_key=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True)
    theme = Column(String(10), nullable=False, default="auto")
    language = Column(String(10), nullable=False, default="en")
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
