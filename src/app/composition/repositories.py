"""
Shared repository factories.

Repositories used by multiple features. These depend on infrastructure
(database session) but not on other repositories or use cases.

Dependency Level: 2 (Data Access)
- Depends on: infrastructure.py (get_database_session)
- Used by: features/*.py

Repository Usage Matrix:
- UserRepository: auth, user, dashboard
- StoryRepository: stories, refinement, dashboard
- ClientRepository: clients, projects (cross-feature dependency)

Why Shared?
Repositories that appear in 2+ features are centralized here to eliminate
duplication and establish a single source of truth for data access patterns.

Feature-specific repositories (used by only one feature) remain in their
feature's composition file.

Usage:
    from src.app.composition import get_user_repository, get_story_repository

    async def my_use_case_factory(
        user_repo: UserRepository = Depends(get_user_repository),
    ):
        return MyUseCase(user_repo)
"""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.composition.infrastructure import get_database_session
from src.app.features.clients.domain.repositories.client_repository import ClientRepository
from src.app.features.clients.infrastructure.repositories.client_repository_impl import ClientRepositoryImpl
from src.app.features.stories.domain.repositories.story_repository import StoryRepository
from src.app.features.stories.infrastructure.repositories.story_repository_impl import StoryRepositoryImpl
from src.app.features.user.domain.repositories.user_repository import UserRepository
from src.app.features.user.infrastructure.repositories.user_repository_impl import UserRepositoryImpl
from src.app.features.workspaces.domain.repositories.workspace_repository import WorkspaceRepository
from src.app.features.workspaces.infrastructure.repositories.workspace_repository_impl import WorkspaceRepositoryImpl


async def get_user_repository(
    session: AsyncSession = Depends(get_database_session),
) -> UserRepository:
    """
    User repository factory (shared across multiple features).

    Used by:
    - auth: Login/register operations, user validation
    - user: Profile management, password changes
    - dashboard: User statistics and activity queries

    The UserRepository is one of the most frequently used repositories in the
    system, as user context is required for most authenticated operations.

    Args:
        session: Request-scoped database session from infrastructure layer

    Returns:
        UserRepository: User repository interface implementation
    """

    return UserRepositoryImpl(session)


async def get_story_repository(
    session: AsyncSession = Depends(get_database_session),
) -> StoryRepository:
    """
    Story repository factory (shared across multiple features).

    Used by:
    - stories: CRUD operations for user stories
    - refinement: Approval of refined stories (saves them as stories)
    - dashboard: Story statistics and metrics

    This is the primary data access layer for user story entities. The repository
    is shared because both manual story creation (stories feature) and AI-generated
    story approval (refinement feature) operate on the same Story domain entity.

    This function uses FastAPI's Depends() for DI. For contexts where Depends()
    is not available (e.g., auth dependencies), use build_story_repository() instead.

    Args:
        session: Request-scoped database session from infrastructure layer

    Returns:
        StoryRepository: Story repository interface implementation
    """

    return StoryRepositoryImpl(session)


def build_story_repository(session: AsyncSession) -> StoryRepository:
    """
    Plain factory for StoryRepository (no FastAPI Depends dependency).

    Use this outside of FastAPI DI resolution for route handler closures
    that need inline repository access (e.g., authorization checks).

    Args:
        session: SQLAlchemy async session (already resolved)

    Returns:
        StoryRepository: Story repository implementation
    """

    return StoryRepositoryImpl(session)


async def get_client_repository(
    session: AsyncSession = Depends(get_database_session),
) -> ClientRepository:
    """
    Client repository factory (shared across multiple features).

    Used by:
    - clients: CRUD operations for client organizations
    - projects: Client validation on project create/update

    Cross-Feature Dependency:
    This is the only cross-feature repository dependency in the system.
    Projects feature depends on ClientRepository to enforce referential integrity:
    when creating/updating a project, the system validates that the client_id
    refers to an existing client before persisting the project.

    This dependency is intentional and represents a legitimate business rule:
    "A project must belong to a valid client organization."

    Args:
        session: Request-scoped database session from infrastructure layer

    Returns:
        ClientRepository: Client repository interface implementation
    """

    return ClientRepositoryImpl(session)


async def get_workspace_repository(
    session: AsyncSession = Depends(get_database_session),
) -> WorkspaceRepository:
    """
    Workspace repository factory (shared by auth registration and user profile/login responses).

    Args:
        session: Request-scoped database session from infrastructure layer

    Returns:
        WorkspaceRepository: Workspace repository interface implementation
    """

    return WorkspaceRepositoryImpl(session)
