"""
Token revocation service for managing revoked/used refresh tokens.

Enforces single-use refresh-token rotation: once a refresh token has been
exchanged, its identifier is recorded here so a replay is rejected. Storage
is pluggable via TokenRevocationRepository: an in-memory implementation
(default, used in tests and single-instance runs) and a SQL-backed one
(src/app/features/auth/infrastructure/repositories/sql_token_revocation_repository.py,
wired in production via composition/infrastructure.py) so revocations survive
a restart and are shared across multiple App Runner instances.
"""

import asyncio
import hashlib
from abc import ABC, abstractmethod
from datetime import UTC, datetime, timedelta


def hash_token(token: str) -> str:
    """Digest a token for storage so raw bearer tokens never sit at rest."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


class TokenRevocationRepository(ABC):
    """Storage port for revoked-token identifiers, keyed by token hash."""

    @abstractmethod
    async def add(self, token_hash: str, expires_at: datetime) -> bool:
        """Record the hash; return False if it was already recorded (e.g. by a concurrent request)."""

    @abstractmethod
    async def contains(self, token_hash: str) -> bool: ...

    @abstractmethod
    async def clear_all(self) -> None: ...

    @abstractmethod
    async def count(self) -> int: ...


class InMemoryTokenRevocationRepository(TokenRevocationRepository):
    """Process-local storage. Lost on restart; not shared across instances."""

    def __init__(self) -> None:
        self._revoked_tokens: dict[str, datetime] = {}

    async def add(self, token_hash: str, expires_at: datetime) -> bool:
        self._cleanup_expired()
        is_new = token_hash not in self._revoked_tokens
        self._revoked_tokens[token_hash] = expires_at
        return is_new

    async def contains(self, token_hash: str) -> bool:
        self._cleanup_expired()
        return token_hash in self._revoked_tokens

    async def clear_all(self) -> None:
        self._revoked_tokens.clear()

    async def count(self) -> int:
        self._cleanup_expired()
        return len(self._revoked_tokens)

    def _cleanup_expired(self) -> None:
        now = datetime.now(UTC)
        expired = [token_hash for token_hash, expiry in self._revoked_tokens.items() if expiry <= now]
        for token_hash in expired:
            del self._revoked_tokens[token_hash]


class TokenRevocationService:
    """Service for tracking revoked and used refresh tokens."""

    def __init__(self, repository: TokenRevocationRepository | None = None):
        """
        Args:
            repository: Storage backend. Defaults to in-memory (tests,
                single-instance runs). Pass a SQL-backed repository in
                production so revocations survive restarts and multiple
                instances.
        """
        self._repository = repository or InMemoryTokenRevocationRepository()
        self._lock = asyncio.Lock()

    async def revoke_token(self, token: str, ttl_minutes: int = 10080) -> bool:
        """
        Mark a token as revoked.

        Args:
            token: The refresh token to revoke (stored as a hash, never raw)
            ttl_minutes: Time-to-live in minutes (default: 7 days for refresh tokens)

        Returns:
            True if this call revoked the token, False if it was already revoked
        """
        async with self._lock:
            expiry = datetime.now(UTC) + timedelta(minutes=ttl_minutes)
            return await self._repository.add(hash_token(token), expiry)

    async def is_revoked(self, token: str) -> bool:
        """
        Check if a token has been revoked.

        Args:
            token: The token to check

        Returns:
            True if token is revoked, False otherwise
        """
        async with self._lock:
            return await self._repository.contains(hash_token(token))

    async def clear_all(self) -> None:
        """Clear all revoked tokens (useful for testing)."""
        async with self._lock:
            await self._repository.clear_all()

    async def get_revoked_count(self) -> int:
        """
        Get count of currently revoked tokens (for monitoring).

        Returns:
            Number of revoked tokens in storage
        """
        async with self._lock:
            return await self._repository.count()


# Singleton instance
_token_revocation_service: TokenRevocationService = TokenRevocationService()


def get_token_revocation_service() -> TokenRevocationService:
    """
    Get the singleton token revocation service instance.

    Returns:
        TokenRevocationService singleton
    """
    return _token_revocation_service
