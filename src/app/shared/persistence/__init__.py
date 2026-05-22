"""Persistence layer: database engine, session, and base model."""

from src.app.shared.persistence.base_model import Base, BaseModel
from src.app.shared.persistence.engine_factory import get_engine, close_engine

# Session is imported lazily to avoid circular imports
# with model modules that depend on Base.
# Use: from src.app.shared.persistence.db_session import get_database_session

__all__ = [
    "Base",
    "BaseModel",
    "get_engine",
    "close_engine",
]
