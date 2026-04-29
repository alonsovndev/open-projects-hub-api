from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

import jwt

from src.shared.utils.log_util import log


class JWTHandler:
    """
    Handles JWT token creation, validation, and decoding.
    Uses HS256 algorithm with symmetric key.
    """

    def __init__(
        self,
        secret_key: str,
        algorithm: str = "HS256",
        expiration_minutes: int = 1440,
    ):
        """
        Args:
            secret_key: Secret key for signing tokens
            algorithm: JWT algorithm (default: HS256)
            expiration_minutes: Token expiration time in minutes (default: 24 hours)
        """
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.expiration_minutes = expiration_minutes

    def create_access_token(
        self,
        user_id: str,
        email: str,
        role: str,
        additional_claims: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Creates a JWT access token with user claims.

        Args:
            user_id: User's unique identifier
            email: User's email address
            role: User's role (ADMIN or USER)
            additional_claims: Optional additional claims to include

        Returns:
            Encoded JWT token string
        """
        now = datetime.now(tz=timezone.utc)
        expires_at = now + timedelta(minutes=self.expiration_minutes)

        payload: Dict[str, Any] = {
            "sub": user_id,
            "email": email,
            "role": role,
            "iat": now,
            "exp": expires_at,
        }

        if additional_claims:
            payload.update(additional_claims)

        token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
        log.info(f"JWT token created for user {user_id} with role {role}")

        return token

    def decode_access_token(self, token: str) -> Dict[str, Any]:
        """
        Decodes and validates a JWT token.

        Args:
            token: JWT token string

        Returns:
            Dictionary containing token payload

        Raises:
            jwt.ExpiredSignatureError: If token has expired
            jwt.InvalidTokenError: If token is invalid
        """
        try:
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm],
            )
            return payload
        except jwt.ExpiredSignatureError:
            log.warning("Attempted to decode expired JWT token")
            raise
        except jwt.InvalidTokenError as e:
            log.warning(f"Invalid JWT token: {str(e)}")
            raise

    def verify_token(self, token: str) -> bool:
        """
        Verifies if a token is valid without raising exceptions.

        Args:
            token: JWT token string

        Returns:
            True if valid, False otherwise
        """
        try:
            self.decode_access_token(token)
            return True
        except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
            return False
