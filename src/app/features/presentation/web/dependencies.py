from typing import AsyncGenerator, Any
from functools import lru_cache

from fastapi.params import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.config.app_config import AppConfig
from src.app.features.application.use_cases.create_user import CreateUserUseCase
from src.app.features.application.use_cases.get_user_by_id import GetUserByIdUseCase
from src.app.features.application.use_cases.login_user import LoginUserUseCase
from src.app.features.infrastructure.repository.user_repository_impl import UserRepositoryImpl
from src.app.features.presentation.web.auth_dependencies import get_jwt_handler
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


# Use Case Dependencies
async def get_login_use_case(
    session: AsyncSession = Depends(get_database_session),
) -> LoginUserUseCase:
    """
    Dependency to get LoginUserUseCase with injected dependencies.
    
    Directly provides the use case to controllers (no service layer).
    """
    user_repository = UserRepositoryImpl(session)
    jwt_handler = get_jwt_handler()
    return LoginUserUseCase(user_repository, jwt_handler)


async def get_create_user_use_case(
    session: AsyncSession = Depends(get_database_session),
) -> CreateUserUseCase:
    """
    Dependency to get CreateUserUseCase with injected dependencies.
    
    Directly provides the use case to controllers (no service layer).
    """
    user_repository = UserRepositoryImpl(session)
    return CreateUserUseCase(user_repository)


async def get_user_by_id_use_case(
    session: AsyncSession = Depends(get_database_session),
) -> GetUserByIdUseCase:
    """
    Dependency to get GetUserByIdUseCase with injected dependencies.
    
    Directly provides the use case to controllers (no service layer).
    """
    user_repository = UserRepositoryImpl(session)
    return GetUserByIdUseCase(user_repository)
