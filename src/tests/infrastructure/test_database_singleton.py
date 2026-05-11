"""
Test to verify database connection singleton pattern.

This test ensures that the database connection manager is created only once
and reused across multiple requests, preventing connection pool exhaustion.
"""
import pytest
from src.app.shared.presentation.dependencies import get_db_connection


def test_get_db_connection_returns_singleton():
    """
    Test that get_db_connection returns the same instance on multiple calls.
    
    This is critical for preventing connection pool exhaustion.
    """
    # Get the connection manager twice
    conn1 = get_db_connection()
    conn2 = get_db_connection()
    
    # They should be the exact same object (same memory address)
    assert conn1 is conn2, "Database connection should be a singleton"
    assert id(conn1) == id(conn2), "Should have the same object ID"


def test_get_db_connection_engine_is_same():
    """
    Test that the SQLAlchemy engine is the same across multiple calls.
    """
    conn1 = get_db_connection()
    conn2 = get_db_connection()
    
    # The engine should also be the same object
    assert conn1.engine is conn2.engine, "SQLAlchemy engine should be shared"


def test_get_db_connection_creates_only_once():
    """
    Test that the connection manager logs creation only once.
    
    Note: This is a behavioral test. In production, you should monitor
    logs to ensure you only see "Creating singleton PostgresDbConnection instance" once.
    """
    # Clear any cached connections
    get_db_connection.cache_clear()
    
    # First call should create the connection
    conn1 = get_db_connection()
    assert conn1 is not None
    
    # Second call should return cached instance
    conn2 = get_db_connection()
    assert conn1 is conn2
    
    # Third call should also return cached instance
    conn3 = get_db_connection()
    assert conn1 is conn3


@pytest.mark.asyncio
async def test_multiple_sessions_share_same_engine():
    """
    Test that multiple sessions use the same underlying engine.
    
    This simulates what happens across multiple HTTP requests.
    """
    from src.app.shared.presentation.dependencies import get_database_session
    
    sessions_info = []
    
    # Simulate 3 concurrent requests getting sessions
    async for session1 in get_database_session():
        sessions_info.append({
            'session_id': id(session1),
            'engine_id': id(session1.bind)
        })
        break  # Exit the async generator
    
    async for session2 in get_database_session():
        sessions_info.append({
            'session_id': id(session2),
            'engine_id': id(session2.bind)
        })
        break
    
    async for session3 in get_database_session():
        sessions_info.append({
            'session_id': id(session3),
            'engine_id': id(session3.bind)
        })
        break
    
    # Sessions should be different objects (each request gets its own)
    assert sessions_info[0]['session_id'] != sessions_info[1]['session_id']
    assert sessions_info[1]['session_id'] != sessions_info[2]['session_id']
    
    # But all sessions should share the same engine (singleton)
    assert sessions_info[0]['engine_id'] == sessions_info[1]['engine_id']
    assert sessions_info[1]['engine_id'] == sessions_info[2]['engine_id']
    
    print("✅ All sessions share the same engine - singleton pattern working correctly!")
