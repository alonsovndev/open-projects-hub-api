"""Database engine factory with config-driven driver selection."""

import asyncio

from src.app.config.app_config import AppConfig
from src.app.shared.logging import get_logger
from src.app.shared.persistence.db_connection import DbConnection
from src.app.shared.persistence.in_memory import InMemoryDbConnection
from src.app.shared.persistence.postgres import PostgresDbConnection

log = get_logger(__name__)


_engine_instance: DbConnection | None = None


def get_engine() -> DbConnection:
    """
    Factory function: returns the correct DbConnection based on config.
    Singleton: same instance reused across all requests.
    """
    global _engine_instance
    if _engine_instance is not None:
        return _engine_instance

    config = AppConfig.instance()
    driver = config.get_config("persistence.driver", "postgresql")

    if driver == "postgresql":
        postgres_config = config.get_config("persistence.postgres", {})
        if not postgres_config:
            # Fallback to legacy postgres: section
            postgres_config = config.get_config("postgres", {})
        _engine_instance = PostgresDbConnection(postgres_config)
        return _engine_instance

    if driver == "in-memory":
        _engine_instance = InMemoryDbConnection()
        return _engine_instance

    raise ValueError(f"Unknown persistence driver: {driver}")


def close_engine() -> None:
    """Dispose the engine and reset the singleton for clean shutdown."""
    global _engine_instance
    if _engine_instance is None:
        return

    conn = _engine_instance
    _engine_instance = None

    try:
        loop = asyncio.get_running_loop()
        loop.create_task(conn.close())
    except RuntimeError:
        # No running loop (e.g. during sync shutdown); run synchronously
        asyncio.run(conn.close())
