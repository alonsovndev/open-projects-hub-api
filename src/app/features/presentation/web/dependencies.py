from typing import AsyncGenerator, Any

from fastapi.params import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.config.app_config import AppConfig
from src.app.features.application.services.user_service import UserService
from src.app.features.infrastructure.repository.user_repository_impl import UserRepositoryImpl
from src.shared.infrastructure.config.postgres_db_conn import PostgresDbConnection
from src.shared.utils.config_util import get_config_value

app_config: dict = AppConfig.instance().config


async def get_database_session() -> AsyncGenerator[Any, Any]:
    """
    Dependency to get a database session.
    """
    postgres_config = get_config_value(app_config, "postgres", {})
    postgres_db_session_manager = PostgresDbConnection(postgres_config)

    async with postgres_db_session_manager.get_session() as session:
        yield session



async def get_user_service(session: AsyncSession = Depends(get_database_session)) -> UserService:
    """
    Dependency to get UserService with proper session management.
    """

    user_repository = UserRepositoryImpl(session)

    return UserService(user_repository)