"""
Test to verify database connection singleton pattern.

This test ensures that the database connection manager is created only once
and reused across multiple requests, preventing connection pool exhaustion.
"""

import pytest

from src.app.shared.persistence.engine_factory import get_engine


def test_get_engine_returns_singleton():
    """
    Test that get_engine returns the same instance on multiple calls.

    This is critical for preventing connection pool exhaustion.
    """
    conn1 = get_engine()
    conn2 = get_engine()

    assert conn1 is conn2, "Database connection should be a singleton"
    assert id(conn1) == id(conn2), "Should have the same object ID"


def test_get_engine_engine_is_same():
    """
    Test that the SQLAlchemy engine is the same across multiple calls.
    """
    conn1 = get_engine()
    conn2 = get_engine()

    assert conn1.engine is conn2.engine, "SQLAlchemy engine should be shared"


@pytest.mark.asyncio
async def test_multiple_sessions_share_same_engine():
    """
    Test that multiple sessions use the same underlying engine.

    This simulates what happens across multiple HTTP requests.
    """
    from src.app.shared.persistence.db_session import get_database_session

    sessions_info = []

    async for session1 in get_database_session():
        sessions_info.append(
            {
                "session_id": id(session1),
                "engine_id": id(session1.bind),
            }
        )
        break

    async for session2 in get_database_session():
        sessions_info.append(
            {
                "session_id": id(session2),
                "engine_id": id(session2.bind),
            }
        )
        break

    async for session3 in get_database_session():
        sessions_info.append(
            {
                "session_id": id(session3),
                "engine_id": id(session3.bind),
            }
        )
        break

    # Sessions should be different objects (each request gets its own)
    assert sessions_info[0]["session_id"] != sessions_info[1]["session_id"]
    assert sessions_info[1]["session_id"] != sessions_info[2]["session_id"]

    # But all sessions should share the same engine (singleton)
    assert sessions_info[0]["engine_id"] == sessions_info[1]["engine_id"]
    assert sessions_info[1]["engine_id"] == sessions_info[2]["engine_id"]
