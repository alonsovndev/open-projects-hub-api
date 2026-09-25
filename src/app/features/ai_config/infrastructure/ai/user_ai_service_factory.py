"""Builds an AIService bound to a user's own provider key."""

from src.app.config.app_config import AppConfig
from src.app.features.ai_config.domain.value_objects.ai_provider import AIProvider
from src.app.features.ai_config.infrastructure.ai.openai_compatible_service import OpenAICompatibleService
from src.app.features.refinement.infrastructure.ai.ai_service import AIService
from src.app.features.refinement.infrastructure.ai.gemini_service import GeminiService


_OPENAI_BASE_URL = "https://api.openai.com/v1"
_DEEPSEEK_BASE_URL = "https://api.deepseek.com/v1"


def create_user_ai_service(provider: AIProvider, api_key: str) -> AIService:
    """
    Build a provider client for a refinement run charged to the user's own key.

    Unlike the platform service in `composition/infrastructure.py`, these are never cached:
    each carries one user's decrypted key and must not outlive the request that built it.

    Args:
        provider: The provider the key belongs to.
        api_key: The user's decrypted provider key.

    Returns:
        An AIService ready to generate stories against that provider.
    """
    config = AppConfig.instance()

    match provider:
        case AIProvider.GEMINI:
            return GeminiService(
                api_key=api_key,
                model=config.get_config("ai.gemini_model", "gemini-2.5-flash"),
            )
        case AIProvider.OPENAI:
            return OpenAICompatibleService(
                api_key=api_key,
                model=config.get_config("ai.openai_model", "gpt-4o-mini"),
                base_url=_OPENAI_BASE_URL,
                provider_label=AIProvider.OPENAI.value,
            )
        case AIProvider.DEEPSEEK:
            return OpenAICompatibleService(
                api_key=api_key,
                model=config.get_config("ai.deepseek_model", "deepseek-chat"),
                base_url=_DEEPSEEK_BASE_URL,
                provider_label=AIProvider.DEEPSEEK.value,
            )
