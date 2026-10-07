"""
Router registration for FastAPI application.

Centralizes API route registration with versioning and tagging.
"""

from src.app.features.ai_config.presentation.ai_config_routes import router as ai_config_router
from src.app.features.auth.presentation.auth_routes import router as auth_router
from src.app.features.backlog.presentation.backlog_routes import router as backlog_router
from src.app.features.client_review.presentation.client_review_routes import router as client_review_router
from src.app.features.clients.presentation.client_routes import router as client_router
from src.app.features.dashboard.presentation.dashboard_routes import router as dashboard_router
from src.app.features.projects.presentation.project_routes import router as project_router
from src.app.features.refinement.presentation.refinement_routes import router as refinement_router
from src.app.features.stories.presentation.story_routes import router as story_router
from src.app.features.user.presentation.user_routes import router as user_router
from src.app.features.workspaces.presentation.workspace_routes import router as workspace_router


def register_routers(app) -> None:
    """
    Register all feature routers with the FastAPI application.

    All routes are versioned under /v1 prefix for API stability.
    Routes are grouped by domain feature with appropriate tags.

    Args:
        app: FastAPI application instance
    """
    # Authentication routes
    app.include_router(auth_router, prefix="/v1/auth", tags=["Authentication"])

    # User management routes
    app.include_router(user_router, prefix="/v1/users", tags=["Users"])

    # AI credit balance and provider API key routes (self-service, so they share the
    # /v1/users prefix; their /me/* paths do not collide with the user router's)
    app.include_router(ai_config_router, prefix="/v1/users", tags=["AI Credits & API Keys"])

    # Workspace routes (rename the caller's own workspace)
    app.include_router(workspace_router, prefix="/v1/workspaces", tags=["Workspaces"])

    # Client management routes
    app.include_router(client_router, prefix="/v1/clients", tags=["Clients"])

    # Project management routes
    app.include_router(project_router, prefix="/v1/projects", tags=["Projects"])

    # Backlog view and Markdown export routes (project-scoped, so they share the
    # /v1/projects prefix; their paths do not collide with the project router's)
    app.include_router(backlog_router, prefix="/v1/projects", tags=["Backlog & Export"])

    # Story management routes
    app.include_router(story_router, prefix="/v1/stories", tags=["Stories"])

    # AI Refinement routes
    app.include_router(refinement_router, prefix="/v1", tags=["AI Refinement"])

    # Dashboard routes
    app.include_router(dashboard_router, prefix="/v1/dashboard", tags=["Dashboard"])

    # Client Review: public, read-only, access-code based (no token)
    app.include_router(client_review_router, prefix="/v1/viewer", tags=["Client Review"])
