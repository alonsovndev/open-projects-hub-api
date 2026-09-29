"""SQL-level proof that tenant queries filter by workspace.

Compiles the statements the repositories actually send, so a filter dropped during a
refactor fails here even though every mocked use-case test would still pass.
"""

from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from sqlalchemy.dialects import postgresql

from src.app.features.clients.infrastructure.repositories.client_repository_impl import ClientRepositoryImpl
from src.app.features.dashboard.infrastructure.repositories.dashboard_repository import DashboardRepositoryImpl
from src.app.features.projects.infrastructure.repositories.project_repository_impl import ProjectRepositoryImpl
from src.app.features.refinement.infrastructure.repositories.story_draft_repository_impl import StoryDraftRepositoryImpl
from src.app.features.stories.infrastructure.repositories.story_repository_impl import StoryRepositoryImpl


WORKSPACE_ID = uuid4()


def capturing_session():
    session = AsyncMock()
    captured = []

    async def execute(stmt):
        captured.append(stmt)
        result = MagicMock()
        result.scalars.return_value.all.return_value = []
        result.scalar_one_or_none.return_value = None
        result.one_or_none.return_value = None
        result.all.return_value = []
        result.scalar_one.return_value = 0
        result.scalar.return_value = 0
        row = MagicMock(total_projects=0, active_projects=0, total_stories=0, completed_stories=0, assigned_stories=0)
        result.one.return_value = row
        return result

    session.execute = execute
    return session, captured


def compiled(stmt) -> str:
    return str(stmt.compile(dialect=postgresql.dialect(), compile_kwargs={"literal_binds": True}))


SCOPED_CALLS = [
    ("clients.find_by_id", ClientRepositoryImpl, lambda repo: repo.find_by_id(uuid4(), workspace_id=WORKSPACE_ID)),
    ("clients.find_all", ClientRepositoryImpl, lambda repo: repo.find_all(workspace_id=WORKSPACE_ID)),
    ("clients.count", ClientRepositoryImpl, lambda repo: repo.count(workspace_id=WORKSPACE_ID)),
    (
        "clients.find_by_email",
        ClientRepositoryImpl,
        lambda repo: repo.find_by_email("a@b.co", workspace_id=WORKSPACE_ID),
    ),
    ("clients.delete", ClientRepositoryImpl, lambda repo: repo.delete(uuid4(), workspace_id=WORKSPACE_ID)),
    ("projects.find_by_id", ProjectRepositoryImpl, lambda repo: repo.find_by_id(uuid4(), workspace_id=WORKSPACE_ID)),
    ("projects.find_all", ProjectRepositoryImpl, lambda repo: repo.find_all(workspace_id=WORKSPACE_ID)),
    ("projects.count", ProjectRepositoryImpl, lambda repo: repo.count(workspace_id=WORKSPACE_ID)),
    ("projects.exists", ProjectRepositoryImpl, lambda repo: repo.exists(uuid4(), workspace_id=WORKSPACE_ID)),
    ("projects.delete", ProjectRepositoryImpl, lambda repo: repo.delete(uuid4(), workspace_id=WORKSPACE_ID)),
    (
        "projects.has_active_projects_for_client",
        ProjectRepositoryImpl,
        lambda repo: repo.has_active_projects_for_client(uuid4(), workspace_id=WORKSPACE_ID),
    ),
    (
        "projects.delete_archived_by_client",
        ProjectRepositoryImpl,
        lambda repo: repo.delete_archived_by_client(uuid4(), workspace_id=WORKSPACE_ID),
    ),
    (
        "projects.count_active_by_workspace",
        ProjectRepositoryImpl,
        lambda repo: repo.count_active_by_workspace(WORKSPACE_ID),
    ),
    ("stories.find_by_id", StoryRepositoryImpl, lambda repo: repo.find_by_id(uuid4(), workspace_id=WORKSPACE_ID)),
    ("stories.find_all", StoryRepositoryImpl, lambda repo: repo.find_all(workspace_id=WORKSPACE_ID)),
    ("stories.count", StoryRepositoryImpl, lambda repo: repo.count(workspace_id=WORKSPACE_ID)),
    ("stories.delete", StoryRepositoryImpl, lambda repo: repo.delete(uuid4(), workspace_id=WORKSPACE_ID)),
    ("drafts.find_by_id", StoryDraftRepositoryImpl, lambda repo: repo.find_by_id(uuid4(), workspace_id=WORKSPACE_ID)),
    (
        "drafts.find_by_project",
        StoryDraftRepositoryImpl,
        lambda repo: repo.find_by_project(uuid4(), workspace_id=WORKSPACE_ID),
    ),
    (
        "drafts.count_by_project",
        StoryDraftRepositoryImpl,
        lambda repo: repo.count_by_project(uuid4(), workspace_id=WORKSPACE_ID),
    ),
    ("drafts.delete", StoryDraftRepositoryImpl, lambda repo: repo.delete(uuid4(), workspace_id=WORKSPACE_ID)),
]


@pytest.mark.asyncio
@pytest.mark.parametrize(("label", "repository_class", "call"), SCOPED_CALLS, ids=[c[0] for c in SCOPED_CALLS])
async def test_query_filters_by_workspace(label, repository_class, call):
    session, captured = capturing_session()

    await call(repository_class(session))

    assert captured, f"{label} sent no statement"
    assert f"workspace_id = '{WORKSPACE_ID}'" in compiled(captured[0]), compiled(captured[0])


@pytest.mark.asyncio
async def test_dashboard_counts_only_the_workspace():
    session, captured = capturing_session()

    await DashboardRepositoryImpl(session).get_aggregated_stats(workspace_id=WORKSPACE_ID, user_id=uuid4())

    sql = compiled(captured[0])
    # Once for the project counts, once for the story counts joined through projects.
    assert sql.count(f"projects.workspace_id = '{WORKSPACE_ID}'") == 2, sql
