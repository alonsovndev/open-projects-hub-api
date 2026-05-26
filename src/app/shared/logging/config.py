"""Logging configuration dataclasses and loader."""

from dataclasses import dataclass, field

from src.app.config.app_config import AppConfig


@dataclass
class OutputConfig:
    """Configuration for a single logging output."""

    type: str  # "console" or "file"
    path: str | None = None
    max_bytes: int | None = None
    backup_count: int | None = None


@dataclass
class LoggingConfig:
    """Top-level logging configuration."""

    level: str = "INFO"
    format: str = "text"  # "text" or "json"
    outputs: list[OutputConfig] = field(default_factory=list)


def load_logging_config() -> LoggingConfig:
    """Read logging config from AppConfig and return a LoggingConfig instance."""
    config = AppConfig.instance()

    level = config.get_config("logging.level", "INFO")
    fmt = config.get_config("logging.format", "text")
    raw_outputs = config.get_config("logging.outputs", [])

    outputs = []
    for out in raw_outputs:
        outputs.append(
            OutputConfig(
                type=out.get("type", "console"),
                path=out.get("path"),
                max_bytes=out.get("max_bytes"),
                backup_count=out.get("backup_count"),
            )
        )

    return LoggingConfig(level=level, format=fmt, outputs=outputs)
