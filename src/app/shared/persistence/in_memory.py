"""In-memory SQLite connection for tests (no PostgreSQL required)."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

from src.app.shared.logging import get_logger
from src.app.shared.persistence.db_connection import DbConnection


log = get_logger(__name__)


class InMemoryDbConnection(DbConnection):
    """In-memory SQLite connection for tests (no PostgreSQL required)."""

    def __init__(self):
        self._db_url = "sqlite+aiosqlite:///:memory:"

        log.info("Initializing in-memory SQLite engine for tests...")
        self._engine: AsyncEngine = create_async_engine(
            self._db_url,
            echo=False,
        )

        log.info("Initializing async sessionmaker (in-memory)...")
        self._async_session = async_sessionmaker(
            bind=self._engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

    @property
    def engine(self) -> AsyncEngine:
        return self._engine

    @asynccontextmanager
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        session = self._async_session()
        try:
            yield session
        finally:
            await session.close()

    async def close(self) -> None:
        log.info("Closing in-memory SQLite engine...")
        await self._engine.dispose()
