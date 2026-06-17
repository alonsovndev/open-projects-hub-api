"""PostgreSQL async connection using asyncpg driver."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy.exc import OperationalError, TimeoutError
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

from src.app.shared.logging import get_logger
from src.app.shared.persistence.db_connection import DbConnection


log = get_logger(__name__)


class PostgresDbConnection(DbConnection):
    """PostgreSQL async connection using asyncpg driver."""

    def __init__(self, postgres_config: dict):
        self._db_username: str = postgres_config["username"]
        self._db_password: str = postgres_config["password"]
        self._db_host: str = postgres_config["host"]
        self._db_port: int = int(postgres_config.get("port", 5432))
        self._db_name: str = postgres_config["dbname"]

        self._echo: bool = postgres_config.get("echo", False)
        self._pool_size: int = int(postgres_config.get("pool_size", 10))
        self._max_overflow: int = int(postgres_config.get("max_overflow", 10))
        self._pool_timeout: int = int(postgres_config.get("pool_timeout", 30))
        self._pool_pre_ping: bool = postgres_config.get("pool_pre_ping", True)

        self._db_url = (
            f"postgresql+asyncpg://{self._db_username}:"
            f"{self._db_password}@{self._db_host}:"
            f"{self._db_port}/{self._db_name}"
        )

        log.info("Initializing PostgreSQL async engine...")
        self._engine: AsyncEngine = create_async_engine(
            self._db_url,
            echo=self._echo,
            pool_size=self._pool_size,
            max_overflow=self._max_overflow,
            pool_timeout=self._pool_timeout,
            pool_pre_ping=self._pool_pre_ping,
        )

        log.info("Initializing async sessionmaker...")
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
        except TimeoutError as e:
            log.error("Database connection pool exhausted.")
            raise Exception("Too many requests. Please try again later.") from e
        except OperationalError as e:
            log.error(f"Database connection error: {e}")
            raise Exception("Database connection failed.") from e
        finally:
            await session.close()

    async def close(self) -> None:
        log.info("Closing PostgreSQL engine...")
        await self._engine.dispose()
