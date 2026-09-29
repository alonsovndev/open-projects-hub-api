"""Tests for how SMTP credentials flow from env vars through config into the email sender."""

from typing import Any

import pytest
from pyaml_env import parse_config

from src.app.composition.infrastructure import get_email_sender
from src.app.config.app_config import AppConfig
from src.app.config.paths import Paths


class FakeConfig:
    def __init__(self, smtp_section: dict[str, Any]):
        self._config = {"smtp": smtp_section}

    def get_config(self, key: str, default: Any = None) -> Any:
        value: Any = self._config
        try:
            for part in key.split("."):
                value = value[part]
            return value
        except (KeyError, TypeError):
            return default


@pytest.fixture
def use_smtp_config(monkeypatch):
    def apply(smtp_section: dict[str, Any]) -> None:
        monkeypatch.setattr(AppConfig, "instance", classmethod(lambda _cls: FakeConfig(smtp_section)))
        get_email_sender.cache_clear()

    yield apply
    get_email_sender.cache_clear()


@pytest.mark.parametrize("environment", ["local", "dev", "container", "prod"])
def test_smtp_credentials_resolve_from_env(monkeypatch, environment):
    monkeypatch.setenv("SMTP_USERNAME", "resend")
    monkeypatch.setenv("SMTP_PASSWORD", "re_secret")

    smtp_section = parse_config(path=str(Paths.CONFIG_DIR / f"config_{environment}.yml"))["smtp"]

    assert smtp_section["username"] == "resend"
    assert smtp_section["password"] == "re_secret"


def test_unset_credentials_become_empty(use_smtp_config):
    use_smtp_config({"host": "localhost", "port": 1025, "username": "N/A", "password": "N/A"})

    sender = get_email_sender()

    assert sender.username == ""
    assert sender.password == ""


def test_set_credentials_are_passed_through(use_smtp_config):
    use_smtp_config({"host": "smtp.resend.com", "port": 587, "username": "resend", "password": "re_secret"})

    sender = get_email_sender()

    assert sender.username == "resend"
    assert sender.password == "re_secret"
