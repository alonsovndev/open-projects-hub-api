from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

import jwt

from src.app.shared.utils.log_util import log


class JWTSecretError(Exception):
    """Raised when JWT secret key is invalid or insecure."""
    pass


class JWTHandler:
    """
    Handles JWT token creation, validation, and decoding.
    Uses HS256 algorithm with symmetric key.
    """
    
    # Common weak/default secrets to reject
    WEAK_SECRETS = {
        "secret",
        "your-secret-key-here",
        "changeme",
        "default",
        "test",
        "password",
        "12345",
        "supersecret",
    }

    def __init__(
        self,
        secret_key: str,
        algorithm: str = "HS256",
        expiration_minutes: int = 1440,
        validate_secret: bool = True,
    ):
        """
        Args:
            secret_key: Secret key for signing tokens
            algorithm: JWT algorithm (default: HS256)
            expiration_minutes: Token expiration time in minutes (default: 24 hours)
            validate_secret: Whether to validate secret strength (default: True, disable for tests)
        
        Raises:
            JWTSecretError: If secret key is weak or invalid
        """
        if validate_secret:
            self._validate_secret_key(secret_key)
        
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.expiration_minutes = expiration_minutes

    @classmethod
    def _validate_secret_key(cls, secret_key: str) -> None:
        """
        Validates JWT secret key strength.
        
        Requirements:
        - At least 32 characters
        - Not a known weak/default secret
        
        Args:
            secret_key: Secret key to validate
            
        Raises:
            JWTSecretError: If secret is weak or invalid
        """
        if not secret_key or not isinstance(secret_key, str):
            raise JWTSecretError("JWT secret key must be a non-empty string")
        
        if len(secret_key) < 32:
            raise JWTSecretError(
                f"JWT secret key is too short ({len(secret_key)} chars). "
                "Minimum 32 characters required for security."
            )
        
        # Check against known weak secrets (case-insensitive)
        if secret_key.lower() in cls.WEAK_SECRETS:
            raise JWTSecretError(
                f"JWT secret key '{secret_key}' is a known weak/default value. "
                "Please use a strong, randomly generated secret."
            )
        
        log.info("JWT secret key validation passed")

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

