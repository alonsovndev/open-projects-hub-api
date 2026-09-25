"""AI service factory - creates the appropriate AI service based on config."""

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

    Priority order:
    1. `ai.provider: mock` forces MockAIService
    2. `ai.provider` naming gemini/openai/deepseek, when `ai.providers.<name>.api_key` is valid
    3. Gemini if no provider is set and its key is valid
    4. MockAIService for development (no usable key)
    """
    config = AppConfig.instance()

    provider = (config.get_config("ai.provider") or "").lower()

    # Detect placeholder/dummy keys; pyaml_env resolves an unset `!ENV ${VAR}` to "N/A".
    def is_valid_key(key: str) -> bool:
        return bool(
            key
            and key.strip()
            and key != _UNSET_ENV_VALUE
            and not key.startswith("your_")
            and not key.startswith("placeholder")
        )

    if provider == "mock":
        log.info("Using MockAIService for story refinement (explicit config)")
        return MockAIService()

    selected = provider or AIProvider.GEMINI.value
    if selected not in AIProvider:
        log.error(f"Unknown ai.provider '{selected}' in config. Using MockAIService.")
        return MockAIService()

    api_key = config.get_config(f"ai.providers.{selected}.api_key", "")
    if is_valid_key(api_key):
        log.info(f"Using {selected} service for story refinement")
        return create_user_ai_service(AIProvider(selected), api_key)

    log.warning(f"No valid API key configured for AI provider '{selected}'. Using MockAIService for development.")
    return MockAIService()
