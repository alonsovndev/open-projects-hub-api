"""Read a user's AI credit balance."""

from src.app.features.ai_config.application.dtos.ai_config_dto import CreditBalanceResponse
from src.app.features.ai_config.application.mappers.credit_mapper import to_credit_balance_response
from src.app.features.user.domain.exceptions.user_exceptions import UserNotFoundError
from src.app.features.user.domain.repositories.user_repository import UserRepository
from src.app.shared.domain.value_objects.entity_id import EntityId


class GetCreditBalanceUseCase:
    """Returns the caller's remaining free platform credits (FR-010-01)."""

    def __init__(self, user_repository: UserRepository):
        """
        Args:
            user_repository: Repository holding the credit balance on the user record.
        """
        self._user_repository = user_repository

    async def execute(self, user_id: str) -> CreditBalanceResponse:
        """
        Read the balance.

        Args:
            user_id: The authenticated user's UUID string.

        Returns:
            CreditBalanceResponse with remaining and originally granted credits.

        Raises:
            UserNotFoundError: If the user no longer exists.
        """
        user = await self._user_repository.find_by_id(EntityId.from_string(user_id))

        if user is None:
            raise UserNotFoundError(user_id)

        return to_credit_balance_response(user)
