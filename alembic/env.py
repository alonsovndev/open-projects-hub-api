import os
import sys
import asyncio
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context

# Add the project's root directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.app.config.app_config import AppConfig
from src.shared.infrastructure.models.base_model import Base
from src.app.features.infrastructure.models.user_model import UserModel

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
target_metadata = Base.metadata

# Dynamically load database URL from AppConfig
postgres_config: dict = AppConfig.instance().get_config("postgres", {})
db_host = postgres_config.get("host", "")
db_port = postgres_config.get("port", 5432)
db_name = postgres_config.get("dbname", "")
db_user = postgres_config.get("username", "")
db_password = postgres_config.get("password", "")

# Create async database URL
async_db_url = f"postgresql+asyncpg://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
config.set_main_option("sqlalchemy.url", async_db_url)


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle":  "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    """Configure context and run migrations."""
    context.configure(
        connection=connection,
        target_metadata=target_metadata
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Run migrations in async mode."""
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode using async engine."""
    asyncio.run(run_async_migrations())


# Determine which mode to run
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()