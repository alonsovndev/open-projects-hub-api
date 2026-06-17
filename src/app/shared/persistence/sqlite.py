"""SQLite connection for tests (no PostgreSQL required)."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy.exc import OperationalError
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

from src.app.shared.logging import get_logger
from src.app.shared.persistence.db_connection import DbConnection


log = get_logger(__name__)


class SQLiteDbConnection(DbConnection):
    """File-based SQLite connection for tests (no PostgreSQL required)."""

    def __init__(self, sqlite_config: dict):
        db_path: str = sqlite_config.get("db_path", "test.db")
        self._db_url = f"sqlite+aiosqlite:///{db_path}"
        self._echo: bool = sqlite_config.get("echo", False)

        log.info("Initializing SQLite engine for tests at %s...", db_path)
        self._engine: AsyncEngine = create_async_engine(self._db_url, echo=self._echo)

        log.info("Initializing async sessionmaker (SQLite)...")
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
        except OperationalError as e:
            log.error("SQLite error: %s", e)
            raise Exception("Database operation failed.") from e
        finally:
            await session.close()

    async def close(self) -> None:
        log.info("Closing SQLite engine...")
        await self._engine.dispose()
