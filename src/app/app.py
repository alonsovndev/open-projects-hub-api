import os
import traceback
from typing import Callable

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from src.app.config.app_config import AppConfig
from src.app.features.dashboard.presentation.routes.dashboard_routes import router as dashboard_router
from src.app.features.projects.presentation.routes.project_routes import router as project_router
from src.app.features.stories.presentation.routes.story_routes import router as story_router
from src.app.features.user.presentation.routes.auth_routes import router as auth_router
from src.app.features.user.presentation.routes.user_routes import router as user_router
from src.app.shared.infrastructure.rate_limit.rate_limiter import limiter
from src.app.shared.domain.exceptions.domain_exceptions import (
    DomainError,
    NotFoundError,
    ValidationError,
    ConflictError,
)
from src.app.shared.utils.log_util import log

ENV = os.getenv("APP_ENV", "local")

config = AppConfig.instance()
app_name = config.get_config("app.name")
app_version = config.get_config("app.version")

fastApiApp = FastAPI(title=app_name, version=app_version)

# Register rate limiter with FastAPI
fastApiApp.state.limiter = limiter
fastApiApp.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


# Global exception handlers
@fastApiApp.exception_handler(NotFoundError)
async def not_found_error_handler(request: Request, exc: NotFoundError) -> JSONResponse:
    """
    Handle NotFoundError exceptions.
    
    Returns 404 with resource information.
    """
    log.warning(f"Resource not found: {exc.message}")
    return JSONResponse(
        status_code=404,
        content={
            "error": "Not Found",
            "message": exc.message,
            "resource": exc.resource,
            "identifier": exc.identifier,
        },
    )


@fastApiApp.exception_handler(ValidationError)
async def validation_error_handler(request: Request, exc: ValidationError) -> JSONResponse:
    """
    Handle ValidationError exceptions.
    
    Returns 400 with validation error details.
    """
    log.warning(f"Validation error: {exc.message}")
    return JSONResponse(
        status_code=400,
        content={
            "error": "Validation Error",
            "message": exc.message,
        },
    )


@fastApiApp.exception_handler(ConflictError)
async def conflict_error_handler(request: Request, exc: ConflictError) -> JSONResponse:
    """
    Handle ConflictError exceptions.
    
    Returns 409 with conflict details.
    """
    log.warning(f"Conflict error: {exc.message}")
    return JSONResponse(
        status_code=409,
        content={
            "error": "Conflict",
            "message": exc.message,
        },
    )


@fastApiApp.exception_handler(DomainError)
async def domain_error_handler(request: Request, exc: DomainError) -> JSONResponse:
    """
    Handle generic DomainError exceptions.
    
    Returns 422 for business logic errors.
    """
    log.error(f"Domain error: {exc.message}")
    return JSONResponse(
        status_code=422,
        content={
            "error": "Domain Error",
            "message": exc.message,
        },
    )


@fastApiApp.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Handle all unhandled exceptions.
    
    Returns 500 with generic error message (no sensitive details in production).
    """
    log.error(f"Unhandled exception: {str(exc)}")
    log.error(traceback.format_exc())
    
    # In production, don't expose internal error details
    if ENV in ("prod", "production"):
        return JSONResponse(
            status_code=500,
            content={
                "error": "Internal Server Error",
                "message": "An unexpected error occurred. Please try again later.",
            },
        )
    else:
        # In dev/local, provide more details for debugging
        return JSONResponse(
            status_code=500,
            content={
                "error": "Internal Server Error",
                "message": str(exc),
                "type": exc.__class__.__name__,
            },
        )

if ENV not in ("local", "container"):
    fastApiApp.docs_url = None
    fastApiApp.redoc_url = None
    fastApiApp.openapi_url = None


def get_allowed_cors_origins() -> list[str]:
    """
    Get allowed CORS origins from configuration with validation.
    
    Raises:
        ValueError: If wildcard origin is used with credentials enabled
    
    Returns:
        List of allowed origin strings
    """
    origins = config.get_config("cors.origins", [])
    allow_credentials = config.get_config("cors.allow_credentials", False)
    
    # Validate: cannot use wildcard with credentials
    if allow_credentials and ("*" in origins or any("*" in origin for origin in origins)):
        raise ValueError(
            "CORS misconfiguration: Cannot use wildcard origins ('*') with "
            "allow_credentials=True. Specify exact origins or disable credentials."
        )
    
    return origins


# Configure CORS from config
cors_origins = get_allowed_cors_origins()
cors_allow_credentials = config.get_config("cors.allow_credentials", False)
cors_allow_methods = config.get_config("cors.allow_methods", ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"])
cors_allow_headers = config.get_config("cors.allow_headers", ["Authorization", "Content-Type", "Accept"])

fastApiApp.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=cors_allow_credentials,
    allow_methods=cors_allow_methods,
    allow_headers=cors_allow_headers,
)


# Security Headers middleware
@fastApiApp.middleware("http")
async def add_security_headers(request: Request, call_next: Callable) -> Response:
    """
    Add security headers to all responses.
    
    Headers added:
    - Strict-Transport-Security: Enforce HTTPS (HSTS)
    - X-Content-Type-Options: Prevent MIME type sniffing
    - X-Frame-Options: Prevent clickjacking
    - Content-Security-Policy: Restrict resource loading
    - X-XSS-Protection: Enable XSS filter (legacy browsers)
    - Referrer-Policy: Control referrer information
    - Permissions-Policy: Control browser features
    """
    response = await call_next(request)
    
    # HSTS: Force HTTPS for 1 year (only in production)
    if ENV in ("prod", "production"):
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    
    # Prevent MIME type sniffing
    response.headers["X-Content-Type-Options"] = "nosniff"
    
    # Prevent clickjacking
    response.headers["X-Frame-Options"] = "DENY"
    
    # Content Security Policy (restrict to API only, no scripts/styles)
    response.headers["Content-Security-Policy"] = "default-src 'none'; frame-ancestors 'none'"
    
    # XSS Protection (legacy browsers)
    response.headers["X-XSS-Protection"] = "1; mode=block"
    
    # Referrer Policy (don't leak referrer info)
    response.headers["Referrer-Policy"] = "no-referrer"
    
    # Permissions Policy (disable unnecessary browser features)
    response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
    
    return response


# API Version middleware
@fastApiApp.middleware("http")
async def add_api_version_header(request: Request, call_next: Callable) -> Response:
    """Add API version to response headers."""
    response = await call_next(request)
    response.headers["X-API-Version"] = "v1"
    return response

@fastApiApp.get("/")
def read_root():
    return {"message": "Welcome to the API"}


@fastApiApp.get("/health")
async def get_health_check():
    """
    Health check endpoint with database connectivity verification.
    
    Returns:
        - 200: Service healthy (database connected)
        - 503: Service unhealthy (database unreachable)
    """
    from sqlalchemy import text
    from src.app.shared.presentation.dependencies import get_db_connection
    
    health_status = {
        "status": "healthy",
        "service": app_name,
        "version": app_version,
        "database": "disconnected"
    }
    
    try:
        # Attempt database connectivity check with async engine
        db = get_db_connection()
        async with db.engine.connect() as connection:
            await connection.execute(text("SELECT 1"))
            health_status["database"] = "connected"
            return JSONResponse(
                status_code=200,
                content=health_status
            )
    except Exception as e:
        log.error(f"Health check failed: database connectivity error - {str(e)}")
        health_status["status"] = "unhealthy"
        health_status["error"] = "database_unreachable"
        return JSONResponse(
            status_code=503,
            content=health_status
        )

fastApiApp.include_router(auth_router, prefix="/v1/auth", tags=["Authentication"])
# TODO validate best practices for endpoint naming conventions
fastApiApp.include_router(user_router, prefix="/v1/user", tags=["Users"])
fastApiApp.include_router(project_router, prefix="/v1/projects", tags=["Projects"])
fastApiApp.include_router(story_router, prefix="/v1/stories", tags=["Stories"])
fastApiApp.include_router(dashboard_router, prefix="/v1/dashboard", tags=["Dashboard"])
