from datetime import UTC, datetime, timedelta
from typing import Any

import jwt

from src.app.shared.logging import get_logger


log = get_logger(__name__)


class JWTSecretError(Exception):
    """Raised when JWT secret key is invalid or insecure."""


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

    # PyJWT decode options shared by access and refresh token decoders
    _DECODE_OPTIONS: dict[str, object] = {
        "require": ["exp", "iat", "sub", "aud", "iss"],
        "verify_exp": True,
        "verify_aud": True,
        "verify_iss": True,
    }

    def __init__(
        self,
        secret_key: str,
        algorithm: str = "HS256",
        expiration_minutes: int = 1440,
        refresh_expiration_minutes: int = 10080,  # 7 days
        validate_secret: bool = True,
        audience: str | None = None,
        issuer: str | None = None,
    ):
        """
        Args:
            secret_key: Secret key for signing tokens
            algorithm: JWT algorithm (default: HS256)
            expiration_minutes: Access token expiration time in minutes (default: 24 hours)
            refresh_expiration_minutes: Refresh token expiration time in minutes (default: 7 days)
            validate_secret: Whether to validate secret strength (default: True, disable for tests)
            audience: Expected audience claim (default: None, auto-set to "open-projects-hub-api")
            issuer: Expected issuer claim (default: None, auto-set to "open-projects-hub-api")

        Raises:
            JWTSecretError: If secret key is weak or invalid
        """
        if validate_secret:
            self._validate_secret_key(secret_key)

        self.secret_key = secret_key
        self.algorithm = algorithm
        self.expiration_minutes = expiration_minutes
        self.refresh_expiration_minutes = refresh_expiration_minutes
        self.audience = audience or "open-projects-hub-api"
        self.issuer = issuer or "open-projects-hub-api"

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
                f"JWT secret key is too short ({len(secret_key)} chars). Minimum 32 characters required for security."
            )

        # Prevent common weak secrets that are easily guessable
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
        additional_claims: dict[str, Any] | None = None,
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
        now = datetime.now(tz=UTC)
        expires_at = now + timedelta(minutes=self.expiration_minutes)

        payload: dict[str, Any] = {
            "sub": user_id,
            "email": email,
            "role": role,
            "iat": now,
            "exp": expires_at,
            "aud": self.audience,
            "iss": self.issuer,
        }

        if additional_claims:
            payload.update(additional_claims)

        token: str = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
        log.info(f"JWT token created for user {user_id} with role {role}")

        return token

    def create_refresh_token(
        self,
        user_id: str,
        email: str,
        role: str,
    ) -> str:
        """
        Creates a JWT refresh token with longer expiration.

        Args:
            user_id: User's unique identifier
            email: User's email address
            role: User's role (ADMIN or USER)

        Returns:
            Encoded JWT refresh token string
        """
        now = datetime.now(tz=UTC)
        expires_at = now + timedelta(minutes=self.refresh_expiration_minutes)

        payload: dict[str, Any] = {
            "sub": user_id,
            "email": email,
            "role": role,
            "iat": now,
            "exp": expires_at,
            "aud": self.audience,
            "iss": self.issuer,
            "type": "refresh",  # Mark as refresh token
        }

        token: str = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
        log.info(f"JWT refresh token created for user {user_id}")

        return token

    def decode_access_token(self, token: str) -> dict[str, Any]:
        """
        Decodes and validates a JWT token with audience and issuer verification.

        Args:
            token: JWT token string

        Returns:
            Dictionary containing token payload

        Raises:
            jwt.ExpiredSignatureError: If token has expired
            jwt.InvalidAudienceError: If audience claim doesn't match
            jwt.InvalidIssuerError: If issuer claim doesn't match
            jwt.InvalidTokenError: If token is invalid
        """
        try:
            return jwt.decode(  # type: ignore[no-any-return]
                token,
                self.secret_key,
                algorithms=[self.algorithm],
                audience=self.audience,
                issuer=self.issuer,
                options=self._DECODE_OPTIONS,
            )
        except jwt.ExpiredSignatureError:
            log.warning("Attempted to decode expired JWT token")
            raise
        except jwt.InvalidAudienceError:
            log.warning(f"JWT token has invalid audience (expected: {self.audience})")
            raise
        except jwt.InvalidIssuerError:
            log.warning(f"JWT token has invalid issuer (expected: {self.issuer})")
            raise
        except jwt.InvalidTokenError as e:
            log.warning(f"Invalid JWT token: {e!s}")
            raise

    def decode_refresh_token(self, token: str) -> dict[str, Any]:
        """
        Decodes and validates a refresh token with type verification.

        Args:
            token: JWT refresh token string

        Returns:
            Dictionary containing token payload

        Raises:
            jwt.ExpiredSignatureError: If token has expired
            jwt.InvalidTokenError: If token is invalid or not a refresh token
        """
        try:
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm],
                audience=self.audience,
                issuer=self.issuer,
                options=self._DECODE_OPTIONS,
            )

            # Verify this is a refresh token
            if payload.get("type") != "refresh":
                log.warning("Attempted to use non-refresh token for refresh operation")
                raise jwt.InvalidTokenError("Token is not a refresh token")

            return payload  # type: ignore[no-any-return]
        except jwt.ExpiredSignatureError:
            log.warning("Attempted to decode expired refresh token")
            raise
        except jwt.InvalidTokenError as e:
            log.warning(f"Invalid refresh token: {e!s}")
            raise
