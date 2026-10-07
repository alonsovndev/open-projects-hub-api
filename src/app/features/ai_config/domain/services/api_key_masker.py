"""Masking for provider API keys (FR-010-07)."""

# How many trailing characters stay readable so a user can tell two of their own keys
# apart. Four is the figure FR-010-07 fixes.
_VISIBLE_SUFFIX = 4

# Providers prefix their keys with a recognizable marker ("sk-", "sk-proj-", "AIza").
# Keeping a short head makes the mask identifiable without narrowing the secret.
_VISIBLE_PREFIX = 7


class ApiKeyMasker:
    """
    Produces the only representation of a key that ever leaves the backend.

    There is no unmasking counterpart and no plaintext read endpoint: once a key is stored,
    the mask is all the API and the UI can obtain.
    """

    @staticmethod
    def mask(raw_key: str) -> str:
        """
        Mask a raw provider API key for display.

        Args:
            raw_key: The raw provider key.

        Returns:
            A masked form such as `sk-proj-***...c123`. Keys too short to split safely are
            fully masked rather than partially revealed.
        """
        key = raw_key.strip()

        if len(key) <= _VISIBLE_PREFIX + _VISIBLE_SUFFIX:
            return "***"

        return f"{key[:_VISIBLE_PREFIX]}***...{key[-_VISIBLE_SUFFIX:]}"
