"""
Rate limiting configuration for the application.

Provides a centralized limiter instance for applying rate limits to endpoints.
"""

from slowapi import Limiter
from slowapi.util import get_remote_address


# Create a singleton limiter instance
# Uses IP address as the rate limit key
limiter = Limiter(key_func=get_remote_address, default_limits=["100/minute"])
