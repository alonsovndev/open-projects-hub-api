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
    Build a provider client bound to `api_key`, using the provider's configured model.

    Called per request with a user's decrypted key — never cache that result, it must not
    outlive the request. The platform factory also builds its (cached) client through here,
    but with the platform's own key.

    Args:
        provider: The provider the key belongs to.
        api_key: The provider key to authenticate with.

    Returns:
        An AIService ready to generate stories against that provider.
    """
    config = AppConfig.instance()

    match provider:
        case AIProvider.GEMINI:
            return GeminiService(
                api_key=api_key,
                model=config.get_config("ai.providers.gemini.model", "gemini-2.5-flash"),
            )
        case AIProvider.OPENAI:
            return OpenAICompatibleService(
                api_key=api_key,
                model=config.get_config("ai.providers.openai.model", "gpt-4o-mini"),
                base_url=_OPENAI_BASE_URL,
                provider_label=AIProvider.OPENAI.value,
            )
        case AIProvider.DEEPSEEK:
            return OpenAICompatibleService(
                api_key=api_key,
                model=config.get_config("ai.providers.deepseek.model", "deepseek-chat"),
                base_url=_DEEPSEEK_BASE_URL,
                provider_label=AIProvider.DEEPSEEK.value,
            )
