"""AI service factory - creates the platform AI service based on config."""

from src.app.config.app_config import AppConfig
from src.app.features.ai_config.domain.value_objects.ai_provider import AIProvider
from src.app.features.ai_config.infrastructure.ai.user_ai_service_factory import create_user_ai_service
from src.app.features.refinement.infrastructure.ai.ai_service import AIService
from src.app.features.refinement.infrastructure.ai.mock_service import MockAIService
from src.app.shared.logging import get_logger


log = get_logger(__name__)

_UNSET_ENV_VALUE = "N/A"


def create_ai_service() -> AIService:
    """
    Create the platform AI service (spends platform credits) based on application configuration.

    The platform always uses Gemini; users who want another provider bring their own key.

    Priority order:
    1. `ai.provider: mock` forces MockAIService
    2. Gemini, when `ai.providers.gemini.api_key` is valid
    3. MockAIService for development (no usable key)
    """
    config = AppConfig.instance()

    if (config.get_config("ai.provider") or "").lower() == "mock":
        log.info("Using MockAIService for story refinement (explicit config)")
        return MockAIService()

    api_key = config.get_config("ai.providers.gemini.api_key", "")
    # pyaml_env resolves an unset `!ENV ${VAR}` to "N/A"; also reject placeholder keys.
    if (
        api_key
        and api_key.strip()
        and api_key != _UNSET_ENV_VALUE
        and not api_key.startswith("your_")
        and not api_key.startswith("placeholder")
    ):
        log.info("Using gemini service for story refinement")
        return create_user_ai_service(AIProvider.GEMINI, api_key)

    log.warning("No valid Gemini API key configured. Using MockAIService for development.")
    return MockAIService()
