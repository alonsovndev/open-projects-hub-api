"""
RefreshTokenUseCase - Refresh access token using refresh token.
"""

import jwt

from src.app.features.auth.application.dtos.auth_dto import RefreshTokenRequest, RefreshTokenResponse
from src.app.features.user.domain.repositories.user_repository import UserRepository
from src.app.shared.domain.value_objects.email import Email
from src.app.shared.infrastructure.security.jwt_handler import JWTHandler
from src.app.shared.infrastructure.security.token_revocation_service import (
    TokenRevocationService,
    get_token_revocation_service,
)
from src.app.shared.logging import get_logger, set_user_id


class RefreshTokenUseCase:
    """
    Use case for refreshing access tokens using refresh tokens.

    Implements token rotation with single-use refresh tokens:
    - Each refresh generates new access token AND new refresh token
    - Old refresh token is immediately revoked and cannot be reused
    - Prevents token replay attacks and stolen token reuse
    - Honors a forced logout (user.token_version bump) by rejecting tokens
      issued before it, even if otherwise unused and unexpired
    """

    def __init__(
        self,
        user_repository: UserRepository,
        jwt_handler: JWTHandler,
        token_revocation: TokenRevocationService | None = None,
    ):
        self.user_repository = user_repository
        self.jwt_handler = jwt_handler
        self.token_revocation = token_revocation or get_token_revocation_service()

    async def execute(self, payload: RefreshTokenRequest) -> RefreshTokenResponse:
        """
        Refresh access token using refresh token.

        Implements single-use refresh tokens: the old refresh token is
        immediately revoked after use, preventing token reuse attacks.

        Args:
            payload: RefreshTokenRequest with refresh token

        Returns:
            RefreshTokenResponse with new access and refresh tokens

        Raises:
            jwt.ExpiredSignatureError: If refresh token has expired
            jwt.InvalidTokenError: If refresh token is invalid or already used
            ValueError: If user not found
        """
        log = None

        try:
            # Decode and validate refresh token first to get user context
            refresh_payload = self.jwt_handler.decode_refresh_token(payload.refresh_token)

            user_id = str(refresh_payload["sub"])
            email = str(refresh_payload["email"])
            remember_me = bool(refresh_payload.get("remember_me", False))
            log = get_logger(__name__)
            set_user_id(user_id)

            # Check if token has already been used (revoked)
            if await self.token_revocation.is_revoked(payload.refresh_token):
                log.warning("Attempt to reuse revoked refresh token", extra={"event_type": "auth.refresh.token_reused"})
                raise jwt.InvalidTokenError("Refresh token has already been used")

            # Revoke the old refresh token immediately (single-use token). A concurrent request
            # with the same token can pass the check above; only the one that revokes it wins.
            if not await self.token_revocation.revoke_token(payload.refresh_token):
                log.warning("Concurrent reuse of refresh token", extra={"event_type": "auth.refresh.token_reused"})
                raise jwt.InvalidTokenError("Refresh token has already been used")
            log.info("Refresh token revoked", extra={"event_type": "auth.refresh.token_revoked"})

            # Verify user still exists
            user_entity = await self.user_repository.find_by_email(Email(email))

            if not user_entity or not user_entity.is_active:
                log.warning(
                    "Refresh token used for non-existent user",
                    extra={"event_type": "auth.refresh.user_not_found", "email": email},
                )
                raise ValueError("User not found")

            # Verify user_id matches
            if str(user_entity.id) != user_id:
                log.warning(
                    "User ID mismatch in refresh token",
                    extra={"event_type": "auth.refresh.user_id_mismatch", "email": email},
                )
                raise jwt.InvalidTokenError("Invalid user credentials in token")

            # Reject tokens issued before a forced logout (user.token_version bump)
            if int(refresh_payload.get("tv", 0)) != user_entity.token_version:
                log.warning(
                    "Refresh token rejected due to forced logout",
                    extra={"event_type": "auth.refresh.forced_logout", "user_id": str(user_entity.id)},
                )
                raise jwt.InvalidTokenError("Session has been revoked")

            # Generate new access token
            new_access_token = self.jwt_handler.create_access_token(
                user_id=str(user_entity.id),
                email=str(user_entity.email),
                role=user_entity.role.value,
                workspace_id=str(user_entity.workspace_id) if user_entity.workspace_id else None,
            )

            # Generate new refresh token (token rotation) — carries the same
            # remember-me duration forward, sliding the session window
            new_refresh_token = self.jwt_handler.create_refresh_token(
                user_id=str(user_entity.id),
                email=str(user_entity.email),
                role=user_entity.role.value,
                remember_me=remember_me,
                token_version=user_entity.token_version,
            )
            session_expires_at = self.jwt_handler.get_token_expiry(new_refresh_token)

            log.info(
                "Tokens refreshed successfully",
                extra={"event_type": "auth.refresh.success", "user_id": str(user_entity.id)},
            )

            return RefreshTokenResponse(
                access_token=new_access_token,
                refresh_token=new_refresh_token,
                session_expires_at=session_expires_at.isoformat().replace("+00:00", "Z"),
            )

        except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
            raise
        except Exception:
            if log:
                log.exception(
                    "Unexpected error in RefreshTokenUseCase",
                    extra={"event_type": "auth.refresh.unexpected_error"},
                )
            raise
