"""
LogoutUseCase - Server-side session invalidation.
"""

from src.app.features.auth.application.dtos.auth_dto import LogoutResponse, RefreshTokenRequest
from src.app.shared.infrastructure.security.jwt_handler import JWTHandler
from src.app.shared.infrastructure.security.token_revocation_service import (
    TokenRevocationService,
    get_token_revocation_service,
)
from src.app.shared.logging import get_logger, set_user_id


class LogoutUseCase:
    """
    Use case for logging out a user by revoking their refresh token.

    Revokes the presented refresh token server-side so it cannot be replayed
    to mint further access tokens. The current (short-lived) access token
    remains valid until its own natural expiry, consistent with the
    short-expiration mitigation documented in the security architecture.
    """

    def __init__(self, jwt_handler: JWTHandler, token_revocation: TokenRevocationService | None = None):
        self.jwt_handler = jwt_handler
        self.token_revocation = token_revocation or get_token_revocation_service()

    async def execute(self, payload: RefreshTokenRequest) -> LogoutResponse:
        """
        Revoke the given refresh token so it can no longer be used to refresh.

        Args:
            payload: RefreshTokenRequest with the session's refresh token

        Returns:
            LogoutResponse confirming the session was invalidated
        """
        log = get_logger(__name__)

        try:
            refresh_payload = self.jwt_handler.decode_refresh_token(payload.refresh_token)
            set_user_id(str(refresh_payload.get("sub")))
        except Exception:
            # Expired/invalid tokens don't need revoking — logout is idempotent
            # and should never fail just because the client's token already lapsed.
            log.info(
                "Logout requested with an already invalid/expired token",
                extra={"event_type": "auth.logout.stale_token"},
            )
            return LogoutResponse(message="Logged out successfully.")

        await self.token_revocation.revoke_token(payload.refresh_token)
        log.info("User logged out, refresh token revoked", extra={"event_type": "auth.logout.success"})

        return LogoutResponse(message="Logged out successfully.")
