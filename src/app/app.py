"""
FastAPI application bootstrap and configuration.
"""

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.app.config.app_config import AppConfig

# Import all models to ensure SQLAlchemy relationships are properly registered
from src.app.features.clients.infrastructure.models.client_model import ClientModel  # noqa: F401
from src.app.features.projects.infrastructure.models.project_model import ProjectModel  # noqa: F401
from src.app.features.refinement.infrastructure.models.story_draft_model import StoryDraftModel  # noqa: F401
from src.app.features.stories.infrastructure.models.story_model import StoryModel  # noqa: F401
from src.app.features.user.infrastructure.models.user_model import UserModel  # noqa: F401
from src.app.features.user.infrastructure.models.user_preferences_model import UserPreferencesModel  # noqa: F401
from src.app.shared.infrastructure.rate_limit.rate_limiter import limiter
from src.app.shared.logging import CorrelationIdMiddleware, load_logging_config, setup_logging
from src.app.shared.persistence.engine_factory import close_engine, get_engine
from src.app.shared.presentation.exception_handlers import register_exception_handlers
from src.app.shared.presentation.health_checks import register_health_endpoints
from src.app.shared.presentation.middleware import register_middleware
from src.app.shared.presentation.router_registry import register_routers


ENV = os.getenv("APP_ENV", "local")

# Load application configuration
config = AppConfig.instance()
app_name = config.get_config("app.name")
app_version = config.get_config("app.version")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle: setup on startup, cleanup on shutdown."""
    # 1. Setup logging first so all startup logs are captured
    logging_config = load_logging_config()
    setup_logging(logging_config)

    # 2. Initialize database connection pool
    get_engine()

    yield

    # 3. Graceful shutdown: dispose connection pool
    close_engine()


# Initialize FastAPI application
fastApiApp = FastAPI(title=app_name, version=app_version, lifespan=lifespan)

# Register correlation ID middleware (must be before app starts)
fastApiApp.add_middleware(CorrelationIdMiddleware)

# Register rate limiter with FastAPI
fastApiApp.state.limiter = limiter

# Disable API documentation in non-local environments
if ENV not in ("local", "container"):
    fastApiApp.docs_url = None
    fastApiApp.redoc_url = None
    fastApiApp.openapi_url = None


@fastApiApp.get("/")
def read_root():
    """Root endpoint returning welcome message."""
    return {"message": "Welcome to the API"}


# Register application components
register_exception_handlers(fastApiApp)
register_middleware(fastApiApp)
register_health_endpoints(fastApiApp)
register_routers(fastApiApp)
