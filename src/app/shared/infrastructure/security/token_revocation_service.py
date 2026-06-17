"""
Token revocation service for managing revoked/used tokens.

This implementation uses an in-memory store for simplicity.
For production deployments with multiple instances, replace with Redis.
"""

import asyncio
from datetime import UTC, datetime, timedelta


class TokenRevocationService:
    """
    Service for tracking revoked and used refresh tokens.

    In-memory implementation with automatic cleanup.
    For production with multiple instances, replace with Redis:
    - Use Redis SET for revoked tokens
    - Set TTL to match refresh token expiration
    """

    def __init__(self):
        """Initialize the token revocation service with in-memory storage."""
        # Store revoked tokens with their expiration timestamps
        self._revoked_tokens: dict[str, datetime] = {}
        self._lock = asyncio.Lock()

    async def revoke_token(self, token: str, ttl_minutes: int = 10080) -> None:
        """
        Mark a token as revoked.

        Args:
            token: The token to revoke (can be JTI or full token)
            ttl_minutes: Time-to-live in minutes (default: 7 days for refresh tokens)
        """
        async with self._lock:
            expiry = datetime.now(UTC) + timedelta(minutes=ttl_minutes)
            self._revoked_tokens[token] = expiry
            self._cleanup_expired()

    async def is_revoked(self, token: str) -> bool:
        """
        Check if a token has been revoked.

        Args:
            token: The token to check

        Returns:
            True if token is revoked, False otherwise
        """
        async with self._lock:
            self._cleanup_expired()
            return token in self._revoked_tokens

    def _cleanup_expired(self) -> None:
        """Remove expired tokens from storage (internal method)."""
        now = datetime.now(UTC)
        expired_tokens = [token for token, expiry in self._revoked_tokens.items() if expiry <= now]
        for token in expired_tokens:
            del self._revoked_tokens[token]

    async def clear_all(self) -> None:
        """Clear all revoked tokens (useful for testing)."""
        async with self._lock:
            self._revoked_tokens.clear()

    async def get_revoked_count(self) -> int:
        """
        Get count of currently revoked tokens (for monitoring).

        Returns:
            Number of revoked tokens in storage
        """
        async with self._lock:
            self._cleanup_expired()
            return len(self._revoked_tokens)


# Singleton instance
_token_revocation_service: TokenRevocationService = TokenRevocationService()


def get_token_revocation_service() -> TokenRevocationService:
    """
    Get the singleton token revocation service instance.

    Returns:
        TokenRevocationService singleton
    """
    return _token_revocation_service
