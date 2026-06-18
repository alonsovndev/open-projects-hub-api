"""Persistence layer: database engine, session, and declarative base."""

from sqlalchemy.orm import declarative_base

from src.app.shared.persistence.engine_factory import close_engine, get_engine


Base = declarative_base()

__all__ = [
    "Base",
    "close_engine",
    "get_engine",
]
