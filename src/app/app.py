"""
FastAPI application bootstrap and configuration.
"""

import os
from contextlib import asynccontextmanager

import sentry_sdk
from fastapi import FastAPI

from src.app.config.app_config import AppConfig
from src.app.shared.infrastructure.rate_limit.rate_limiter import limiter
from src.app.shared.logging import setup_logging
from src.app.shared.logging.middleware import RequestContextMiddleware
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
app_description = (
    "REST API for Open Projects Hub — project, client, and story management "
    "with JWT authentication and role-based access control. See "
    "[docs/api/README.md](https://github.com/alonsovndev/open-projects-hub-api/"
    "blob/main/docs/api/README.md) for auth flows, pagination, and code examples."
)

# Error tracking (ADR-009). Configured per-environment in config_<env>.yml —
# only config_prod.yml sets a real sentry_dsn today; other environments
# explicitly disable it (console/CloudWatch logs are used there instead).
# Normalize "not configured" cases to None: pyaml_env substitutes the literal
# string "N/A" for an !ENV var with no default that's unset, and sentry-sdk's
# DSN parser raises BadDsn on "" — both would crash startup, not just no-op.
_sentry_dsn = config.get_config("monitoring.sentry_dsn")
if _sentry_dsn in (None, "", "N/A"):
    _sentry_dsn = None

# send_default_pii=False: the SDK must not auto-capture request bodies/headers/
# IPs; user context is set explicitly (internal user ID only) in
# request_logging_middleware.
sentry_sdk.init(
    dsn=_sentry_dsn,
    environment=ENV,
    release=app_version,
    send_default_pii=False,
    traces_sample_rate=config.get_config("monitoring.sentry_traces_sample_rate", 0.1),
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle: setup on startup, cleanup on shutdown."""
    # 1. Setup logging first so all startup logs are captured
    log_level = config.get_config("logging.level", "INFO")
    log_format = config.get_config("logging.format", "json")
    setup_logging(level=log_level, plain_text=(log_format == "text"))

    # 2. Initialize database connection pool
    get_engine()

    yield

    # 3. Graceful shutdown: dispose connection pool
    await close_engine()


# Initialize FastAPI application
fastapi_app = FastAPI(title=app_name, version=app_version, description=app_description, lifespan=lifespan)

# Register correlation ID middleware (must be before app starts)
fastapi_app.add_middleware(RequestContextMiddleware)

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
