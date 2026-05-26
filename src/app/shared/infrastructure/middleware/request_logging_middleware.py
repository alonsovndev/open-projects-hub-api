"""
Request logging middleware with correlation ID support.

Logs every HTTP request with method, path, status, latency, and correlation ID.
"""
import time
import uuid
from typing import Callable

from fastapi import Request, Response
from src.app.shared.logging import get_logger

log = get_logger(__name__)


async def request_logging_middleware(request: Request, call_next: Callable) -> Response:
    """
    Middleware to log all HTTP requests with correlation IDs.
    
    Generates or extracts X-Request-ID header and logs:
    - HTTP method
    - Request path
    - Status code
    - Latency in milliseconds
    
    The X-Request-ID is added to the response headers for client reference
    and included in structured log output.
    
    Args:
        request: FastAPI request object
        call_next: Next middleware/handler in the chain
        
    Returns:
        Response with X-Request-ID header
    """
    # Generate or extract request ID
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    
    # Attach request_id to request state for use in downstream handlers
    request.state.request_id = request_id
    
    # Record start time
    start_time = time.time()
    
    # Process request
    response = await call_next(request)
    
    # Calculate latency
    latency_ms = (time.time() - start_time) * 1000
    
    # Add request ID to response headers
    response.headers["X-Request-ID"] = request_id
    
    # Log request details with structured fields
    log.info(
        f"HTTP request processed",
        extra={
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "latency_ms": round(latency_ms, 2),
            "client_host": request.client.host if request.client else None,
        }
    )
    
    return response
