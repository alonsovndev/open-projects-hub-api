"""Tests for how the platform and user-key AI factories read the `ai.providers` config."""

from typing import Any

import pytest

from src.app.config.app_config import AppConfig
from src.app.features.ai_config.domain.value_objects.ai_provider import AIProvider
from src.app.features.ai_config.infrastructure.ai.user_ai_service_factory import create_user_ai_service
from src.app.features.refinement.infrastructure.ai.ai_factory import create_ai_service
from src.app.features.refinement.infrastructure.ai.gemini_service import GeminiService
from src.app.features.refinement.infrastructure.ai.mock_service import MockAIService


class FakeConfig:
    def __init__(self, ai_section: dict[str, Any]):
        self._config = {"ai": ai_section}

    def get_config(self, key: str, default: Any = None) -> Any:
        value: Any = self._config
        try:
            for part in key.split("."):
                value = value[part]
            return value
        except (KeyError, TypeError):
            return default


def providers_section(gemini: str = "") -> dict[str, Any]:
    return {
        "gemini": {"model": "gemini-test", "api_key": gemini},
        "openai": {"model": "gpt-test"},
        "deepseek": {"model": "deepseek-test"},
    }


@pytest.fixture
def use_ai_config(monkeypatch):
    def apply(ai_section: dict[str, Any]) -> None:
        monkeypatch.setattr(AppConfig, "instance", classmethod(lambda _cls: FakeConfig(ai_section)))

    return apply


def test_mock_provider_returns_mock_even_with_keys(use_ai_config):
    use_ai_config({"provider": "mock", "providers": providers_section(gemini="real-key")})

    assert isinstance(create_ai_service(), MockAIService)


def test_platform_ignores_non_mock_provider_setting(use_ai_config):
    use_ai_config({"provider": "openai", "providers": providers_section(gemini="real-key")})

    assert isinstance(create_ai_service(), GeminiService)


def test_no_provider_auto_detects_gemini(use_ai_config):
    use_ai_config({"providers": providers_section(gemini="real-key")})

    service = create_ai_service()

    assert isinstance(service, GeminiService)
    assert service._model == "gemini-test"


def test_blank_provider_auto_detects_gemini(use_ai_config):
    use_ai_config({"provider": None, "providers": providers_section(gemini="real-key")})

    assert isinstance(create_ai_service(), GeminiService)


@pytest.mark.parametrize("api_key", ["your_gemini_key", "N/A"])
def test_placeholder_or_unset_key_is_not_used(use_ai_config, api_key):
    use_ai_config({"provider": "gemini", "providers": providers_section(gemini=api_key)})

    assert isinstance(create_ai_service(), MockAIService)


@pytest.mark.parametrize(
    ("provider", "expected_model"),
    [(AIProvider.GEMINI, "gemini-test"), (AIProvider.OPENAI, "gpt-test"), (AIProvider.DEEPSEEK, "deepseek-test")],
)
def test_user_factory_reads_model_from_providers_section(use_ai_config, provider, expected_model):
    use_ai_config({"provider": "mock", "providers": providers_section()})

    service = create_user_ai_service(provider, "user-key")

    assert service._model == expected_model
