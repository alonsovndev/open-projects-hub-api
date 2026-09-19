"""
HTTP middleware components for FastAPI application.

Provides security headers, API versioning, and CORS configuration.
"""

import os
from collections.abc import Callable

from fastapi import Request, Response
from fastapi.middleware.cors import CORSMiddleware

from src.app.config.app_config import AppConfig


ENV = os.getenv("APP_ENV", "local")


async def add_security_headers(request: Request, call_next: Callable) -> Response:
    """
    Add security headers to all responses.

    Headers added:
    - Strict-Transport-Security: Enforce HTTPS (HSTS) - production only
    - X-Content-Type-Options: Prevent MIME type sniffing
    - X-Frame-Options: Prevent clickjacking
    - Content-Security-Policy: Restrict resource loading
      * Local/Dev: Allows Swagger UI on /docs endpoint
      * Production: Strict policy on all endpoints (docs disabled)
    - X-XSS-Protection: Enable XSS filter (legacy browsers)
    - Referrer-Policy: Control referrer information
    - Permissions-Policy: Control browser features

    Args:
        request: The incoming HTTP request
        call_next: The next middleware or route handler

    Returns:
        Response with security headers added
    """
    response = await call_next(request)

    # HSTS: Force HTTPS for 1 year (only in production)
    if ENV in ("prod", "production"):
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

    # Prevent MIME type sniffing
    response.headers["X-Content-Type-Options"] = "nosniff"

    # Prevent clickjacking
    response.headers["X-Frame-Options"] = "DENY"

    # Content Security Policy - More permissive in local/dev, strict in production
    # In local/dev: Allow Swagger UI resources on /docs endpoint
    # In production: Strict CSP on all endpoints (no documentation endpoints exposed)
    if ENV in ("local", "dev", "development"):
        # Allow Swagger UI resources for local development
        if request.url.path.startswith(("/docs", "/redoc", "/openapi.json")):
            # Swagger UI requires: CDN resources, inline scripts, and unsafe-eval
            response.headers["Content-Security-Policy"] = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net; "
                "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
                "img-src 'self' data: https://fastapi.tiangolo.com; "
                "font-src 'self' data:; "
                "connect-src 'self'"
            )
        else:
            # Strict CSP for API endpoints (no scripts/styles allowed)
            response.headers["Content-Security-Policy"] = "default-src 'none'; frame-ancestors 'none'"
    else:
        # Production: strict CSP on all endpoints (docs should be disabled in production)
        response.headers["Content-Security-Policy"] = "default-src 'none'; frame-ancestors 'none'"

    # XSS Protection (legacy browsers)
    response.headers["X-XSS-Protection"] = "1; mode=block"

    # Referrer Policy (don't leak referrer info)
    response.headers["Referrer-Policy"] = "no-referrer"

    # Permissions Policy (disable unnecessary browser features)
    response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"

    return response


async def add_api_version_header(request: Request, call_next: Callable) -> Response:
    """
    Add API version to response headers.

    Args:
        request: The incoming HTTP request
        call_next: The next middleware or route handler

    Returns:
        Response with X-API-Version header added
    """
    response = await call_next(request)
    response.headers["X-API-Version"] = "v1"
    return response


def get_allowed_cors_origins() -> list[str]:
    """
    Get allowed CORS origins from configuration with validation.

    Validates that wildcard origins are not used with credentials enabled,
    as this is a security misconfiguration.

    Raises:
        ValueError: If wildcard origin is used with credentials enabled

    Returns:
        List of allowed origin strings
    """
    config = AppConfig.instance()
    origins = config.get_config("cors.origins", [])
    allow_credentials = config.get_config("cors.allow_credentials", False)

    # Validate: cannot use wildcard with credentials
    if allow_credentials and ("*" in origins or any("*" in origin for origin in origins)):
        raise ValueError(
            "CORS misconfiguration: Cannot use wildcard origins ('*') with "
            "allow_credentials=True. Specify exact origins or disable credentials."
        )

    return origins


def configure_cors(app) -> None:
    """
    Configure CORS middleware from application configuration.

    Reads CORS settings from config and adds CORSMiddleware to the application.
    Validates that credentials are not used with wildcard origins.

    Args:
        app: FastAPI application instance

    Raises:
        ValueError: If CORS configuration is invalid
    """
    config = AppConfig.instance()

    cors_origins = get_allowed_cors_origins()
    # Optional, local-dev-only convenience: Vite picks the next free port
    # when the default is busy (5173 -> 5174 -> ...), so a fixed exact-match
    # origin list breaks every time that happens. Only config_local.yml sets
    # this; dev/container/prod keep the exact-match `cors.origins` list.
    cors_origin_regex = config.get_config("cors.origin_regex", None)
    cors_allow_credentials = config.get_config("cors.allow_credentials", False)
    cors_allow_methods = config.get_config("cors.allow_methods", ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"])
    cors_allow_headers = config.get_config("cors.allow_headers", ["Authorization", "Content-Type", "Accept"])

    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_origin_regex=cors_origin_regex,
        allow_credentials=cors_allow_credentials,
        allow_methods=cors_allow_methods,
        allow_headers=cors_allow_headers,
    )


def register_middleware(app) -> None:
    """
    Register all middleware with the FastAPI application.

    Middleware is applied in reverse order of registration (last registered = first executed).
    Order matters for proper request/response processing.

    Args:
        app: FastAPI application instance
    """
    from src.app.shared.infrastructure.middleware.request_logging_middleware import request_logging_middleware

    # Configure CORS (applied last, executed first)
    configure_cors(app)

    # Request logging middleware (with correlation IDs)
    app.middleware("http")(request_logging_middleware)

    # Security headers middleware
    app.middleware("http")(add_security_headers)

    # API version header
    app.middleware("http")(add_api_version_header)
