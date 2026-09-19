"""
Health check endpoints for application monitoring and orchestration.

Provides liveness and readiness probes for Kubernetes deployments,
plus a legacy combined health check for backward compatibility.
"""

from fastapi.responses import JSONResponse
from sqlalchemy import text

from src.app.config.app_config import AppConfig
from src.app.shared.logging import get_logger
from src.app.shared.persistence.engine_factory import get_engine


log = get_logger(__name__)


config = AppConfig.instance()
app_name = config.get_config("app.name")
app_version = config.get_config("app.version")


async def get_health_check():
    """
    Combined health check endpoint (legacy, maintained for backward compatibility).

    For Kubernetes deployments, use /health/live and /health/ready instead.

    This endpoint checks both liveness (process running) and readiness
    (database connectivity), making it suitable for simple deployments
    but less flexible than separate probes.

    Returns:
        JSONResponse:
            - 200: Service healthy (database connected)
            - 503: Service unhealthy (database unreachable)
    """
    health_status = {"status": "healthy", "service": app_name, "version": app_version, "database": "disconnected"}

    try:
        # Attempt database connectivity check with async engine
        db = get_engine()
        async with db.engine.connect() as connection:
            await connection.execute(text("SELECT 1"))
            health_status["database"] = "connected"
            return JSONResponse(status_code=200, content=health_status)
    except Exception as e:
        log.error(f"Health check failed: database connectivity error - {e!s}")
        health_status["status"] = "unhealthy"
        health_status["error"] = "database_unreachable"
        return JSONResponse(status_code=503, content=health_status)


async def get_liveness_check():
    """
    Liveness probe for Kubernetes.

    Indicates whether the application process is running and responsive.
    If this fails, Kubernetes will restart the container.

    This is a lightweight check that doesn't test external dependencies,
    making it fast and preventing unnecessary container restarts due to
    temporary dependency failures.

    Use this for:
    - Detecting deadlocks or hung processes
    - Verifying the application can respond to HTTP requests

    Returns:
        JSONResponse:
            - 200: Process is alive and responsive
    """
    return JSONResponse(status_code=200, content={"status": "alive", "service": app_name, "version": app_version})


async def get_readiness_check():
    """
    Readiness probe for Kubernetes.

    Indicates whether the application is ready to handle traffic.
    Tests connectivity to required dependencies (database).
    If this fails, Kubernetes will stop routing traffic to this pod
    without restarting it, allowing temporary issues to resolve.

    Use this for:
    - Verifying database connectivity before accepting traffic
    - Preventing requests during startup or graceful shutdown
    - Handling temporary dependency outages

    Returns:
        JSONResponse:
            - 200: Service ready (all dependencies healthy)
            - 503: Service not ready (dependencies unavailable)
    """
    readiness_status = {
        "status": "ready",
        "service": app_name,
        "version": app_version,
        "checks": {"database": "disconnected"},
    }

    try:
        # Check database connectivity
        db = get_engine()
        async with db.engine.connect() as connection:
            await connection.execute(text("SELECT 1"))
            readiness_status["checks"]["database"] = "connected"
            return JSONResponse(status_code=200, content=readiness_status)
    except Exception as e:
        log.error(f"Readiness check failed: database connectivity error - {e!s}", extra={"check": "database"})
        readiness_status["status"] = "not_ready"
        readiness_status["checks"]["database"] = "disconnected"
        readiness_status["error"] = "database_unreachable"
        return JSONResponse(status_code=503, content=readiness_status)


def register_health_endpoints(app) -> None:
    """
    Register health check endpoints with the FastAPI application.

    Registers three endpoints:
    - /health: Legacy combined check (backward compatibility)
    - /health/live: Kubernetes liveness probe
    - /health/ready: Kubernetes readiness probe

    Args:
        app: FastAPI application instance
    """
    app.get("/health")(get_health_check)
    app.get("/health/live")(get_liveness_check)
    app.get("/health/ready")(get_readiness_check)
