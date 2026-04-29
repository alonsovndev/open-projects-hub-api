import bcrypt

from src.app.shared.utils.log_util import log


class PasswordHandler:
    """
    Handles password hashing and verification using bcrypt.
    """

    @staticmethod
    def hash_password(plain_password: str) -> str:
        """
        Hashes a plain text password using bcrypt.

        Args:
            plain_password: Plain text password

        Returns:
            Hashed password string
        """
        password_hash = bcrypt.hashpw(
            plain_password.encode("utf-8"),
            bcrypt.gensalt(),
        ).decode("utf-8")

        return password_hash

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """
        Verifies a plain text password against a hashed password.

        Args:
            plain_password: Plain text password to verify
            hashed_password: Hashed password to compare against

        Returns:
            True if password matches, False otherwise
        """
        try:
            result = bcrypt.checkpw(
                plain_password.encode("utf-8"),
                hashed_password.encode("utf-8"),
            )
            return result
        except Exception as e:
            log.error(f"Error verifying password: {str(e)}")
            return False
