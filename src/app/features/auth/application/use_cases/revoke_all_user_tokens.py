"""
RevokeAllUserTokensUseCase - Forced logout across every device.
"""

from src.app.features.user.domain.repositories.user_repository import UserRepository
from src.app.shared.domain.value_objects.entity_id import EntityId
from src.app.shared.logging import get_logger


class RevokeAllUserTokensUseCase:
    """
    Bumps a user's token_version, invalidating every refresh token issued
    before this call. RefreshTokenUseCase rejects any refresh token whose
    embedded token_version no longer matches the user's current one.

    Used internally after a password reset (ConfirmPasswordResetUseCase) so a
    compromised account can't stay logged in elsewhere after recovery.
    """

    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository

    async def execute(self, user_id: EntityId) -> None:
        log = get_logger(__name__)
        user_entity = await self.user_repository.find_by_id(user_id)

        if user_entity is None:
            return

        user_entity.revoke_sessions()
        await self.user_repository.update(user_entity)

        log.info(
            "All sessions revoked for user",
            extra={"event_type": "auth.sessions.revoked_all", "user_id": str(user_id)},
        )
