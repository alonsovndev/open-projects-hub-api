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

from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

from src.app.features.refinement.infrastructure.ai.ai_factory import create_ai_service
from src.app.features.refinement.infrastructure.ai.ai_service import AIService
from src.app.shared.persistence.engine_factory import get_engine


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
    async with db_conn.get_session() as session:
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
        AIService: Gemini AI service or MockAIService based on configuration
    """
    global _ai_service_instance
    if _ai_service_instance is None:
        _ai_service_instance = create_ai_service()
    return _ai_service_instance
