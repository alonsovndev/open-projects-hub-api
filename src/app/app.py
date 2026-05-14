"""
FastAPI application bootstrap and configuration.

This module initializes the FastAPI application and coordinates
registration of routers, middleware, exception handlers, and health checks.
"""
import os

from fastapi import FastAPI

from src.app.config.app_config import AppConfig
from src.app.shared.infrastructure.rate_limit.rate_limiter import limiter
from src.app.shared.presentation.exception_handlers import register_exception_handlers
from src.app.shared.presentation.middleware import register_middleware
from src.app.shared.presentation.health_checks import register_health_endpoints
from src.app.shared.presentation.router_registry import register_routers


ENV = os.getenv("APP_ENV", "local")

# Load application configuration
config = AppConfig.instance()
app_name = config.get_config("app.name")
app_version = config.get_config("app.version")

# Initialize FastAPI application
fastApiApp = FastAPI(title=app_name, version=app_version)

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
