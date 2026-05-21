"""
Router registration for FastAPI application.

Centralizes API route registration with versioning and tagging.
"""
from src.app.features.dashboard.presentation.routes.dashboard_routes import router as dashboard_router
from src.app.features.projects.presentation.routes.project_routes import router as project_router
from src.app.features.stories.presentation.routes.story_routes import router as story_router
from src.app.features.user.presentation.routes.auth_routes import router as auth_router
from src.app.features.user.presentation.routes.user_routes import router as user_router
from src.app.features.clients.presentation.client_routes import router as client_router
from src.app.features.refinement.presentation.routes import router as refinement_router


def register_routers(app) -> None:
    """
    Register all feature routers with the FastAPI application.
    
    All routes are versioned under /v1 prefix for API stability.
    Routes are grouped by domain feature with appropriate tags.
    
    Args:
        app: FastAPI application instance
    """
    # Authentication routes
    app.include_router(
        auth_router,
        prefix="/v1/auth",
        tags=["Authentication"]
    )
    
    # User management routes
    app.include_router(
        user_router,
        prefix="/v1/users",
        tags=["Users"]
    )
    
    # Client management routes
    app.include_router(
        client_router,
        prefix="/v1",
        tags=["Clients"]
    )
    
    # Project management routes
    app.include_router(
        project_router,
        prefix="/v1/projects",
        tags=["Projects"]
    )
    
    # Story management routes
    app.include_router(
        story_router,
        prefix="/v1/stories",
        tags=["Stories"]
    )
    
    # AI Refinement routes
    app.include_router(
        refinement_router,
        prefix="/v1",
        tags=["AI Refinement"]
    )
    
    # Dashboard routes
    app.include_router(
        dashboard_router,
        prefix="/v1/dashboard",
        tags=["Dashboard"]
    )
