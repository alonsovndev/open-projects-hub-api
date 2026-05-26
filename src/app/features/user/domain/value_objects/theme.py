"""
Theme value object for user preferences.
"""

from enum import Enum


class Theme(str, Enum):
    """Theme preference enum."""

    LIGHT = "light"
    DARK = "dark"
    AUTO = "auto"

    @property
    def value(self) -> str:
        """Return the lowercase theme value."""
        return self._value_
