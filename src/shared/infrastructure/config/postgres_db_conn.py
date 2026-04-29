from sqlalchemy.exc import TimeoutError, OperationalError
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, AsyncEngine, async_sessionmaker
from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator

from src.shared.utils.config_util import get_config_value
from src.shared.utils.log_util import log


class PostgresDbConnection:
    """
    Manages an asynchronous SQLAlchemy database connection with session handling.
    """

    def __init__(self, postgres_config: dict):

        self.db_username: str = get_config_value(postgres_config, 'username')
        self.db_password: str = get_config_value(postgres_config, "password")
        self.db_host: str = get_config_value(postgres_config, "host")
        self.db_port: int = get_config_value(postgres_config, "port", 5432, expected_type=int)
        self.db_name: str = get_config_value(postgres_config, "dbname")

        # Optional configuration with defaults
        self.echo: bool = get_config_value(postgres_config, "echo", default=False)
        self.pool_size: int = int(get_config_value(postgres_config, "pool-size", default=10))
        self.max_over_flow: int = int(get_config_value(postgres_config, "max-over-flow", default=5))
        self.pool_timeout: int = int(get_config_value(postgres_config, "pool-timeout", default=30))

        self.db_url = (
            f"postgresql+asyncpg://{self.db_username}:"
            f"{self.db_password}@{self.db_host}:"
            f"{self.db_port}/{self.db_name}"
        )

        log.info("Initializing SQLAlchemy asynchronous database engine...")
        self.engine: AsyncEngine = create_async_engine(
            self.db_url,
            echo=self.echo,
            pool_size=self.pool_size,
            max_overflow=self.max_over_flow,
            pool_timeout=self.pool_timeout,
        )

        log.info("Initializing SQLAlchemy asynchronous sessionmaker...")
        self.async_session = async_sessionmaker(
            bind=self.engine,
            class_=AsyncSession,
            expire_on_commit=False
        )

    @asynccontextmanager
    async def get_session(self) -> AsyncGenerator[AsyncSession | Any, Any]:
        """
        Provides an asynchronous SQLAlchemy session with context management.

        Yields:
            AsyncSession: A new SQLAlchemy session.
        """
        session = self.async_session()
        try:
            yield session
        except TimeoutError:
            log.error("Database connection pool exhausted.")
            raise Exception("Too many requests. Please try again later.")
        except OperationalError as e:
            log.error(f"Database connection error: {e}")
            raise Exception("Database connection failed.")
        finally:
            await session.close()

    async def close_engine(self):
        """
        Closes the SQLAlchemy engine.
        """
        log.info("Closing SQLAlchemy engine...")

        await self.engine.dispose()
