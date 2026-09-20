"""SQL-level tests for the backlog query.

These compile the statement the repository builds rather than mocking it away. A mocked
repository cannot catch a type error that only PostgreSQL raises, which is exactly how the
priority ordering shipped broken once: `case(value=...)` bound its whens as bare VARCHAR,
and Postgres refuses to compare VARCHAR to the `storypriority` enum.
"""

from datetime import date
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from sqlalchemy.dialects import postgresql

from src.app.features.stories.domain.queries.backlog_query import BacklogQuery
from src.app.features.stories.domain.value_objects.story_status import StoryStatus
from src.app.features.stories.infrastructure.repositories.story_repository_impl import StoryRepositoryImpl


def build_session_capturing_statements():
    """An AsyncSession stub that records the statements it is handed."""
    session = AsyncMock()
    captured = []

    async def execute(stmt):
        captured.append(stmt)
        result = MagicMock()
        result.scalars.return_value.all.return_value = []
        result.scalar_one.return_value = 0
        return result

    session.execute = execute
    return session, captured


def compile_to_postgres(stmt) -> str:
    """Render a statement as the PostgreSQL driver would receive it."""
    return str(stmt.compile(dialect=postgresql.dialect(), compile_kwargs={"literal_binds": True}))


@pytest.mark.asyncio
async def test_priority_ordering_compares_against_the_enum_column():
    """The CASE must compare the column itself, not an untyped VARCHAR literal."""
    session, captured = build_session_capturing_statements()
    repository = StoryRepositoryImpl(session)

    await repository.find_backlog(BacklogQuery(project_id=uuid4()))

    sql = compile_to_postgres(captured[0])
    order_by = sql.split("ORDER BY")[1]

    # The shorthand renders "CASE stories.priority WHEN 'high' THEN ...", which is the
    # form Postgres rejects. The comparison form renders "WHEN stories.priority = 'high'".
    assert "CASE stories.priority WHEN" not in order_by
    assert "stories.priority = 'high'" in order_by


@pytest.mark.asyncio
async def test_backlog_orders_by_priority_then_oldest_first():
    """Test that the reading order is priority, then age."""
    session, captured = build_session_capturing_statements()
    repository = StoryRepositoryImpl(session)

    await repository.find_backlog(BacklogQuery(project_id=uuid4()))

    order_by = compile_to_postgres(captured[0]).split("ORDER BY")[1]

    assert order_by.index("'high'") < order_by.index("'medium'") < order_by.index("'low'")
    assert "stories.created_at ASC" in order_by


@pytest.mark.asyncio
async def test_date_range_is_an_inclusive_calendar_range():
    """dateTo names a whole day, so the upper bound is the start of the next one."""
    session, captured = build_session_capturing_statements()
    repository = StoryRepositoryImpl(session)

    await repository.find_backlog(
        BacklogQuery(
            project_id=uuid4(),
            created_from=date(2026, 1, 1),
            created_to=date(2026, 6, 30),
        )
    )

    sql = compile_to_postgres(captured[0])

    assert "stories.created_at >= '2026-01-01 00:00:00+00:00'" in sql
    assert "stories.created_at < '2026-07-01 00:00:00+00:00'" in sql


@pytest.mark.asyncio
async def test_status_filter_reaches_the_where_clause():
    """Test that a status scope becomes a WHERE predicate."""
    session, captured = build_session_capturing_statements()
    repository = StoryRepositoryImpl(session)

    await repository.find_backlog(BacklogQuery(project_id=uuid4(), status=StoryStatus.DONE))

    assert "stories.status = 'done'" in compile_to_postgres(captured[0])


@pytest.mark.asyncio
async def test_count_shares_the_scope_but_drops_the_pagination():
    """A count that inherited LIMIT/OFFSET would cap the reported total."""
    session, captured = build_session_capturing_statements()
    repository = StoryRepositoryImpl(session)
    query = BacklogQuery(project_id=uuid4(), status=StoryStatus.TODO, limit=10, offset=20)

    await repository.count_backlog(query)

    sql = compile_to_postgres(captured[0])

    assert "count(" in sql.lower()
    assert "stories.status = 'todo'" in sql
    assert "LIMIT" not in sql.upper()
    assert "OFFSET" not in sql.upper()


@pytest.mark.asyncio
async def test_backlog_is_scoped_to_one_project():
    """Test that the project predicate is always present."""
    session, captured = build_session_capturing_statements()
    repository = StoryRepositoryImpl(session)
    project_id = uuid4()

    await repository.find_backlog(BacklogQuery(project_id=project_id))

    assert f"stories.project_id = '{project_id}'" in compile_to_postgres(captured[0])
