"""AI service factory - creates the appropriate AI service based on config."""

from src.app.config.app_config import AppConfig
from src.app.features.refinement.infrastructure.ai.ai_service import AIService
from src.app.features.refinement.infrastructure.ai.gemini_service import GeminiService
from src.app.features.refinement.infrastructure.ai.mock_service import MockAIService
from src.app.shared.logging import get_logger


log = get_logger(__name__)


def create_ai_service() -> AIService:
    """
    Create an AI service instance based on application configuration.

    Priority order:
    1. Explicit provider setting in config
    2. Gemini if GEMINI_API_KEY is configured
    3. MockAIService for development (no API keys)
    """
    config = AppConfig.instance()

    provider = config.get_config("ai.provider", "").lower()

    gemini_key = config.get_config("ai.gemini_api_key", "")
    gemini_model = config.get_config("ai.gemini_model", "gemini-2.0-flash")

    # Detect placeholder/dummy keys
    def is_valid_key(key: str) -> bool:
        return bool(key and key.strip() and not key.startswith("your_") and not key.startswith("placeholder"))

    # Respect explicit provider setting
    if provider == "mock":
        log.info("Using MockAIService for story refinement (explicit config)")
        return MockAIService()

    if provider == "gemini" and is_valid_key(gemini_key):
        log.info(f"Using Gemini service for story refinement (model: {gemini_model})")
        return GeminiService(api_key=gemini_key, model=gemini_model)

    # Auto-detect if no explicit provider
    if is_valid_key(gemini_key):
        log.info("Using Gemini service for story refinement (auto-detected)")
        return GeminiService(api_key=gemini_key, model=gemini_model)

    log.warning("No valid GEMINI_API_KEY configured. Using MockAIService for development.")
    return MockAIService()
