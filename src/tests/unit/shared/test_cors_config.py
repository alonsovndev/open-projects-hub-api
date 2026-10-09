from pathlib import Path
from unittest.mock import MagicMock, patch

from pyaml_env import parse_config

from src.app.shared.presentation.middleware import get_allowed_cors_origins


PROD_CONFIG = Path(__file__).resolve().parents[3] / "app" / "config" / "config_prod.yml"


def _config_with(origins: list[str]) -> MagicMock:
    config = MagicMock()
    config.get_config.side_effect = lambda key, default=None: {
        "cors.origins": origins,
        "cors.allow_credentials": False,
    }.get(key, default)
    return config


def test_comma_separated_origins_are_split():
    config = _config_with(["https://app.example.com, https://admin.example.com"])

    with patch("src.app.shared.presentation.middleware.AppConfig.instance", return_value=config):
        assert get_allowed_cors_origins() == ["https://app.example.com", "https://admin.example.com"]


def test_list_origins_are_kept():
    config = _config_with(["http://localhost:5173"])

    with patch("src.app.shared.presentation.middleware.AppConfig.instance", return_value=config):
        assert get_allowed_cors_origins() == ["http://localhost:5173"]


def test_prod_allow_credentials_defaults_to_real_false(monkeypatch):
    monkeypatch.delenv("CORS_ALLOW_CREDENTIALS", raising=False)

    config = parse_config(path=str(PROD_CONFIG))

    assert config["cors"]["allow_credentials"] is False
