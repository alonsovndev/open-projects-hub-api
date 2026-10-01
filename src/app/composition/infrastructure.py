"""
Infrastructure-level dependencies.

Provides database sessions, external service clients, and singleton infrastructure.
These have no dependencies on repositories or use cases.

Dependency Level: 1 (Foundation)
- No dependencies on other composition modules
- Used by: repositories.py, features/*.py

Lifecycle Management:
- Database sessions: Request-scoped (new per HTTP request)
- AI service: Application-scoped singleton (created once, reused)

Usage:
    from src.app.composition import get_database_session, get_ai_service

    async def my_factory(
        session: AsyncSession = Depends(get_database_session),
    ):
        return MyRepository(session)
"""

from collections.abc import AsyncGenerator
from functools import lru_cache

from sqlalchemy.ext.asyncio import AsyncSession

from src.app.config.app_config import AppConfig
from src.app.features.refinement.infrastructure.ai.ai_factory import create_ai_service
from src.app.features.refinement.infrastructure.ai.ai_service import AIService
from src.app.shared.infrastructure.email.email_sender import EmailSender
from src.app.shared.infrastructure.email.smtp_email_sender import SmtpEmailSender
from src.app.shared.infrastructure.security.jwt_handler import JWTHandler
from src.app.shared.persistence.engine_factory import get_engine


_UNSET_ENV_VALUE = "N/A"


@lru_cache(maxsize=1)
def get_jwt_handler() -> JWTHandler:
    """
    Cached singleton factory for JWTHandler.

    Creates a single JWTHandler instance from application config
    and caches it for the application lifetime.
    """
    config = AppConfig.instance()
    secret_key = config.get_config("jwt.secret_key")
    algorithm = config.get_config("jwt.algorithm", "HS256")
    expiration = config.get_config("jwt.access_token_expire_minutes", 1440)

    if not secret_key:
        raise ValueError("JWT secret_key not configured")

    return JWTHandler(
        secret_key=secret_key,
        algorithm=algorithm,
        expiration_minutes=int(expiration),
    )


@lru_cache(maxsize=1)
def get_email_sender() -> EmailSender:
    """
    Cached singleton factory for EmailSender.

    Scoped to password-reset-code delivery (EPIC-2); see SmtpEmailSender's
    docstring for why it stays minimal until EPIC-9-BE-001 lands.
    """
    config = AppConfig.instance()

    # pyaml_env resolves an unset `!ENV ${VAR}` to "N/A"; an empty default
    # (`${VAR:}`) isn't an option because pyaml_env never substitutes it.
    def credential(key: str) -> str:
        value = config.get_config(key, "")
        return "" if value == _UNSET_ENV_VALUE else value

    host = credential("smtp.host") or "localhost"
    from_address = credential("smtp.from_address") or "no-reply@open-projects-hub.local"
    # Send failures are swallowed by the use cases, so a malformed sender would
    # otherwise only surface as a log line while users never get their code.
    if "@" not in from_address:
        raise ValueError(f"smtp.from_address must be an email address, got {from_address!r}")

    return SmtpEmailSender(
        host=host,
        port=int(config.get_config("smtp.port", 587)),
        username=credential("smtp.username"),
        password=credential("smtp.password"),
        from_address=from_address,
        use_tls=bool(config.get_config("smtp.use_tls", True)),
    )


async def get_database_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Provides request-scoped database session.

    Lifecycle: New session per HTTP request, automatically committed/rolled back.
    FastAPI Depends() handles session cleanup via context manager.

    The session is yielded from an async context manager which ensures:
    - Automatic commit on successful completion
    - Automatic rollback on exceptions
    - Proper connection pool management

    Usage:
        async def my_repository_factory(
            session: AsyncSession = Depends(get_database_session),
        ):
            return MyRepositoryImpl(session)

    Yields:
        AsyncSession: SQLAlchemy async session for database operations
    """
    db_conn = get_engine()
    async with db_conn.get_session() as session:  # type: AsyncSession
        yield session


# Singleton AI service (application-scoped)
# Module-level cache ensures single instance across all requests
_ai_service_instance: AIService | None = None


async def get_ai_service() -> AIService:
    """
    Provides singleton AI service instance.

    Lifecycle: Created once at first request, reused for application lifetime.
    Thread-safe via module-level caching pattern.

    The AI service is expensive to create (loads models, validates API keys),
    so we maintain a single instance for the entire application lifecycle.

    Implementation:
    - First call: Creates service via ai_factory and caches
    - Subsequent calls: Returns cached instance
    - Configuration: Determined by AppConfig (Gemini vs Mock)

    Usage:
        async def my_use_case_factory(
            ai_service: AIService = Depends(get_ai_service),
        ):
            return GenerateStoriesUseCase(ai_service)

    Returns:
        AIService: The provider named by `ai.provider`, or MockAIService based on configuration
    """
    global _ai_service_instance
    if _ai_service_instance is None:
        _ai_service_instance = create_ai_service()
    return _ai_service_instance
