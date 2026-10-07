"""Workspace limits read from application config."""

from src.app.config.app_config import AppConfig
from src.app.features.workspaces.domain.value_objects.workspace_limits import WorkspaceLimits


def _limit(key: str, default: int) -> int:
    value = AppConfig.instance().get_config(f"workspace_limits.{key}")
    return default if value is None else int(value)


def get_workspace_limits() -> WorkspaceLimits:
    return WorkspaceLimits(
        max_users=_limit("max_users", 5),
        ai_credits_ceiling=_limit("ai_credits_ceiling", 25),
        credits_per_user=_limit("credits_per_user", 5),
    )
