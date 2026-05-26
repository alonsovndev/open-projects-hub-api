"""Abstract interface for database connections."""

from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession


class DbConnection(ABC):
    """Interface for database connections."""

    @property
    @abstractmethod
    def engine(self) -> AsyncEngine:
        """Return the SQLAlchemy async engine."""

    @abstractmethod
    @asynccontextmanager
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Yield an async session with error handling."""

    @abstractmethod
    async def close(self) -> None:
        """Dispose the engine for graceful shutdown."""
