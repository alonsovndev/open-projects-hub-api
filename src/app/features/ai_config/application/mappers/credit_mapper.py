"""Entity to DTO mapping for AI credit balances."""

from src.app.features.ai_config.application.dtos.ai_config_dto import CreditBalanceResponse
from src.app.features.user.domain.entities.user_entity import UserEntity


def to_credit_balance_response(user: UserEntity) -> CreditBalanceResponse:
    """Describe a user's remaining and originally granted free credits."""
    return CreditBalanceResponse(
        credits=user.ai_credits_remaining,
        total_granted=user.ai_credits_granted,
    )
