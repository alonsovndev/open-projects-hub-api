from functools import lru_cache

from src.app.application.auth.use_cases import LoginUseCase
from src.app.infrastructure.auth.in_memory_repository import InMemoryUserRepository


@lru_cache
def get_user_repository() -> InMemoryUserRepository:
    return InMemoryUserRepository()


def get_login_use_case() -> LoginUseCase:
    return LoginUseCase(user_repository=get_user_repository())
