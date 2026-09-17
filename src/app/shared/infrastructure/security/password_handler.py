import asyncio

import bcrypt

from src.app.shared.logging import get_logger


log = get_logger(__name__)


class PasswordHandler:
    """
    Handles password hashing and verification using bcrypt.

    Uses asyncio.to_thread() to prevent blocking the event loop during
    CPU-intensive bcrypt operations.
    """

    @staticmethod
    async def hash_password(plain_password: str) -> str:
        """
        Hashes a plain text password using bcrypt asynchronously.

        Runs bcrypt operations in a thread pool to prevent blocking the event loop.

        Args:
            plain_password: Plain text password

        Returns:
            Hashed password string
        """

        def _hash():
            return bcrypt.hashpw(
                plain_password.encode("utf-8"),
                bcrypt.gensalt(),
            ).decode("utf-8")

        return await asyncio.to_thread(_hash)

    @staticmethod
    async def verify_password(plain_password: str, hashed_password: str) -> bool:
        """
        Verifies a plain text password against a hashed password asynchronously.

        Runs bcrypt operations in a thread pool to prevent blocking the event loop.

        Args:
            plain_password: Plain text password to verify
            hashed_password: Hashed password to compare against

        Returns:
            True if password matches, False otherwise
        """
        try:

            def _verify():
                return bcrypt.checkpw(
                    plain_password.encode("utf-8"),
                    hashed_password.encode("utf-8"),
                )

            return await asyncio.to_thread(_verify)
        except Exception as e:
            log.error(f"Error verifying password: {e!s}")
            return False
