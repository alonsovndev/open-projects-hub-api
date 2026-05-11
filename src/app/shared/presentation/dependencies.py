"""
Shared presentation layer dependencies.

Provides common dependencies used across multiple features,
including database session management.
"""
from typing import AsyncGenerator
from functools import lru_cache

from sqlalchemy.ext.asyncio import AsyncSession

from src.app.config.app_config import AppConfig
from src.app.shared.infrastructure.config.postgres_db_conn import PostgresDbConnection
from src.app.shared.utils.config_util import get_config_value
from src.app.shared.utils.log_util import log

app_config: dict = AppConfig.instance().config


@lru_cache(maxsize=1)
def get_db_connection() -> PostgresDbConnection:
    """
    Singleton database connection manager.
    Creates engine once and reuses across all requests.
    
    CRITICAL: This prevents connection pool exhaustion by ensuring
    only one PostgresDbConnection instance (and one SQLAlchemy engine)
    exists for the entire application lifecycle.
    """
    postgres_config = get_config_value(app_config, "postgres", {})
    log.info("Creating singleton PostgresDbConnection instance")
    return PostgresDbConnection(postgres_config)


async def get_database_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency to get a database session.
    
    Reuses the singleton database connection manager to get sessions.
    Each request gets its own session, but all sessions share the same
    connection pool from the singleton engine.
    """
    db_conn = get_db_connection()
    async with db_conn.get_session() as session:
        yield session
