"""
Database integration test fixtures and configuration.

Provides fixtures for running integration tests against a real PostgreSQL database.
Tests in this module use the @pytest.mark.e2e marker and require a running database.
"""
import asyncio
import pytest
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, AsyncEngine, create_async_engine, async_sessionmaker
from sqlalchemy import text

from src.app.shared.infrastructure.models.base_model import Base
from src.app.config.app_config import AppConfig


@pytest.fixture(scope="session")
def event_loop():
    """
    Create event loop for async tests.
    
    Session-scoped to allow sharing database connections across tests.
    """
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def test_engine() -> AsyncGenerator[AsyncEngine, None]:
    """
    Create async database engine for integration tests.
    
    Uses test configuration and creates a fresh database for each test session.
    """
    # Load test configuration
    config = AppConfig.instance(env="test")
    postgres_config = config.get_config("postgres")
    
    # Build database URL
    db_username = postgres_config.get("username", "open-projects-hub-admin")
    db_password = postgres_config.get("password", "test_password")
    db_host = postgres_config.get("host", "localhost")
    db_port = postgres_config.get("port", 5432)
    db_name = postgres_config.get("dbname", "open-projects-hub-db")
    
    db_url = (
        f"postgresql+asyncpg://{db_username}:"
        f"{db_password}@{db_host}:"
        f"{db_port}/{db_name}"
    )
    
    # Create engine with test-optimized settings
    engine = create_async_engine(
        db_url,
        echo=False,  # Reduce noise in test output
        pool_size=5,
        max_overflow=5,
        pool_pre_ping=True,
    )
    
    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    # Cleanup: drop all tables after test session
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    await engine.dispose()


@pytest.fixture(scope="function")
async def db_session(test_engine: AsyncEngine) -> AsyncGenerator[AsyncSession, None]:
    """
    Provide clean database session for each test.
    
    Each test gets a fresh transaction that is rolled back after the test,
    ensuring test isolation without recreating the entire database.
    """
    # Create session factory
    async_session_maker = async_sessionmaker(
        bind=test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    
    # Start a transaction
    async with async_session_maker() as session:
        async with session.begin():
            yield session
            # Rollback happens automatically when exiting context


@pytest.fixture(scope="function")
async def clean_db(db_session: AsyncSession) -> AsyncGenerator[AsyncSession, None]:
    """
    Provide completely clean database for tests that need guaranteed isolation.
    
    Truncates all tables before yielding the session.
    Use this fixture when test isolation via transactions isn't sufficient.
    """
    # Truncate all tables (except alembic_version)
    await db_session.execute(
        text("""
            DO $$ 
            DECLARE
                r RECORD;
            BEGIN
                FOR r IN (
                    SELECT tablename 
                    FROM pg_tables 
                    WHERE schemaname = 'public' 
                    AND tablename != 'alembic_version'
                ) LOOP
                    EXECUTE 'TRUNCATE TABLE ' || quote_ident(r.tablename) || ' CASCADE';
                END LOOP;
            END $$;
        """)
    )
    await db_session.commit()
    
    yield db_session
