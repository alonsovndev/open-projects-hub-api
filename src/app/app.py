"""
FastAPI application bootstrap and configuration.
"""

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.app.config.app_config import AppConfig
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
    await close_engine()


# Initialize FastAPI application
fastapi_app = FastAPI(title=app_name, version=app_version, lifespan=lifespan)

# Register correlation ID middleware (must be before app starts)
fastapi_app.add_middleware(CorrelationIdMiddleware)

# Register rate limiter with FastAPI
fastapi_app.state.limiter = limiter

# Disable API documentation in non-local environments
if ENV not in ("local", "container"):
    fastapi_app.docs_url = None
    fastapi_app.redoc_url = None
    fastapi_app.openapi_url = None


@fastapi_app.get("/")
def read_root():
    """Root endpoint returning welcome message."""
    return {"message": "Welcome to the API"}


# Register application components
register_exception_handlers(fastapi_app)
register_middleware(fastapi_app)
register_health_endpoints(fastapi_app)
register_routers(fastapi_app)
