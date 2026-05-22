"""Database session dependency provider."""

from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

from src.app.shared.persistence.engine_factory import get_engine


async def get_database_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency: yields an async database session."""
    db_conn = get_engine()
    async with db_conn.get_session() as session:
        yield session
