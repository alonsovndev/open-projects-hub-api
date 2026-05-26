"""Phone number value object for client domain."""

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class PhoneNumber:
    """Value object representing a phone number."""

    value: str

    def __post_init__(self):
        """Validate phone number format."""
        if not self._is_valid_phone(self.value):
            raise ValueError(f"Invalid phone number format: {self.value}")

    @staticmethod
    def _is_valid_phone(phone: str) -> bool:
        """Validate phone number format (flexible international format)."""
        # Remove common separators for validation
        cleaned = re.sub(r"[\s\-\(\)\.]", "", phone)
        # Must be 7-15 digits, optionally starting with +
        pattern = r"^\+?\d{7,15}$"
        return bool(re.match(pattern, cleaned))

    def __str__(self) -> str:
        return self.value
